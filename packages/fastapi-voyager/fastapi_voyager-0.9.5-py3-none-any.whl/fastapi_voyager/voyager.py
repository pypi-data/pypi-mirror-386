import inspect
from fastapi import FastAPI, routing
from fastapi_voyager.type_helper import (
    get_core_types,
    full_class_name,
    get_bases_fields,
    is_inheritance_of_pydantic_base,
    get_pydantic_fields,
    get_vscode_link,
    get_source,
    get_type_name,
    update_forward_refs,
    is_non_pydantic_type
)
from pydantic import BaseModel
from fastapi_voyager.type import Route, SchemaNode, Link, Tag, LinkType, FieldType, PK, CoreData
from fastapi_voyager.filter import filter_graph, filter_subgraph
from fastapi_voyager.render import Renderer
import pydantic_resolve.constant as const


class Voyager:
    def __init__(
            self, 
            schema: str | None = None, 
            schema_field: str | None = None,
            show_fields: FieldType = 'single',
            include_tags: list[str] | None = None,
            module_color: dict[str, str] | None = None,
            route_name: str | None = None,
            hide_primitive_route: bool = False,
        ):

        self.routes: list[Route] = []

        self.nodes: list[SchemaNode] = []
        self.node_set: dict[str, SchemaNode] = {}

        self.link_set: set[tuple[str, str]] = set()
        self.links: list[Link] = []

        # store Tag by id, and also keep a list for rendering order
        self.tag_set: dict[str, Tag] = {}
        self.tags: list[Tag] = []

        self.include_tags = include_tags
        self.schema = schema
        self.schema_field = schema_field
        self.show_fields = show_fields if show_fields in ('single','object','all') else 'object'
        self.module_color = module_color or {}
        self.route_name = route_name
        self.hide_primitive_route = hide_primitive_route
    

    def _get_available_route(self, app: FastAPI):
        for route in app.routes:
            if isinstance(route, routing.APIRoute) and route.response_model:
                yield route


    def analysis(self, app: FastAPI):
        """
        1. get routes which return pydantic schema
            1.1 collect tags and routes, add links tag-> route
            1.2 collect response_model and links route -> response_model

        2. iterate schemas, construct the schema/model nodes and their links
        """
        schemas: list[type[BaseModel]] = []

        for route in self._get_available_route(app):
            # check tags
            tags = getattr(route, 'tags', None)
            route_tag = tags[0] if tags else '__default__'
            if self.include_tags and route_tag not in self.include_tags:
                continue

            # add tag if not exists
            tag_id = f'tag__{route_tag}'
            if tag_id not in self.tag_set:
                tag_obj = Tag(id=tag_id, name=route_tag, routes=[])
                self.tag_set[tag_id] = tag_obj
                self.tags.append(tag_obj)

            # add route and create links
            route_id = full_class_name(route.endpoint)
            route_name = route.endpoint.__name__
            route_module = route.endpoint.__module__

            # filter by route_name (route.id) if provided
            if self.route_name is not None and route_id != self.route_name:
                continue

            is_primitive_response = is_non_pydantic_type(route.response_model)
            # filter primitive route if needed
            if self.hide_primitive_route and is_primitive_response:
                continue

            self.links.append(Link(
                source=tag_id,
                source_origin=tag_id,
                target=route_id,
                target_origin=route_id,
                type='tag_route'
            ))

            route_obj = Route(
                id=route_id,
                name=route_name,
                module=route_module,
                response_schema=get_type_name(route.response_model),
                is_primitive=is_primitive_response
            )
            self.routes.append(route_obj)
            # add route into current tag
            self.tag_set[tag_id].routes.append(route_obj)

            # add response_models and create links from route -> response_model
            for schema in get_core_types(route.response_model):
                if schema and issubclass(schema, BaseModel):
                    is_primitive_response = False
                    target_name = full_class_name(schema)
                    self.links.append(Link(
                        source=route_id,
                        source_origin=route_id,
                        target=self.generate_node_head(target_name),
                        target_origin=target_name,
                        type='route_to_schema'
                    ))

                    schemas.append(schema)

        for s in schemas:
            self.analysis_schemas(s)
        
        self.nodes = list(self.node_set.values())


    def add_to_node_set(self, schema):
        """
        1. calc full_path, add to node_set
        2. if duplicated, do nothing, else insert
        2. return the full_path
        """
        full_name = full_class_name(schema)
        bases_fields = get_bases_fields([s for s in schema.__bases__ if is_inheritance_of_pydantic_base(s)])
        
        subset_reference = getattr(schema, const.ENSURE_SUBSET_REFERENCE, None)
        if subset_reference and is_inheritance_of_pydantic_base(subset_reference):
            bases_fields.update(get_bases_fields([subset_reference]))

        if full_name not in self.node_set:
            # skip meta info for normal queries
            self.node_set[full_name] = SchemaNode(
                id=full_name, 
                module=schema.__module__,
                name=schema.__name__,
                fields=get_pydantic_fields(schema, bases_fields)
            )
        return full_name


    def add_to_link_set(
            self, 
            source: str, 
            source_origin: str,
            target: str, 
            target_origin: str,
            type: LinkType
        ) -> bool:
        """
        1. add link to link_set
        2. if duplicated, do nothing, else insert
        """
        pair = (source, target)
        if result := pair not in self.link_set:
            self.link_set.add(pair)
            self.links.append(Link(
                source=source,
                source_origin=source_origin,
                target=target,
                target_origin=target_origin,
                type=type
            ))
        return result


    def analysis_schemas(self, schema: type[BaseModel]):
        """
        1. cls is the source, add schema
        2. pydantic fields are targets, if annotation is subclass of BaseMode, add fields and add links
        3. recursively run walk_schema
        """
        
        update_forward_refs(schema)
        self.add_to_node_set(schema)

        base_fields = set()

        # handle schema inside ensure_subset(schema)
        if subset_reference := getattr(schema,  const.ENSURE_SUBSET_REFERENCE, None):
            if is_inheritance_of_pydantic_base(subset_reference):

                self.add_to_node_set(subset_reference)
                self.add_to_link_set(
                    source=self.generate_node_head(full_class_name(schema)),
                    source_origin=full_class_name(schema),
                    target= self.generate_node_head(full_class_name(subset_reference)), 
                    target_origin=full_class_name(subset_reference),
                    type='subset')
                self.analysis_schemas(subset_reference)

        # handle bases
        for base_class in schema.__bases__:
            if is_inheritance_of_pydantic_base(base_class):
                # collect base class field names to avoid duplicating inherited fields
                try:
                    base_fields.update(getattr(base_class, 'model_fields', {}).keys())
                except Exception:
                    # be defensive in case of unconventional BaseModel subclasses
                    pass
                self.add_to_node_set(base_class)
                self.add_to_link_set(
                    source=self.generate_node_head(full_class_name(schema)),
                    source_origin=full_class_name(schema),
                    target=self.generate_node_head(full_class_name(base_class)),
                    target_origin=full_class_name(base_class),
                    type='parent')
                self.analysis_schemas(base_class)

        # handle fields
        for k, v in schema.model_fields.items():
            # skip fields inherited from base classes
            if k in base_fields:
                continue
            annos = get_core_types(v.annotation)
            for anno in annos:
                if anno and is_inheritance_of_pydantic_base(anno):
                    self.add_to_node_set(anno)
                    # add f prefix to fix highlight issue in vsc graphviz interactive previewer
                    source_name = f'{full_class_name(schema)}::f{k}'
                    if self.add_to_link_set(
                        source=source_name,
                        source_origin=full_class_name(schema),
                        target=self.generate_node_head(full_class_name(anno)),
                        target_origin=full_class_name(anno),
                        type='schema'):
                        self.analysis_schemas(anno)


    def generate_node_head(self, link_name: str):
        return f'{link_name}::{PK}'

    def dump_core_data(self):
        _tags, _routes, _nodes, _links = filter_graph(
            schema=self.schema,
            schema_field=self.schema_field,
            tags=self.tags,
            routes=self.routes,
            nodes=self.nodes,
            links=self.links,
            node_set=self.node_set,
        )
        return CoreData(
            tags=_tags,
            routes=_routes,
            nodes=_nodes,
            links=_links,
            show_fields=self.show_fields,
            module_color=self.module_color,
            schema=self.schema
        )

    def render_dot(self):
        _tags, _routes, _nodes, _links = filter_graph(
            schema=self.schema,
            schema_field=self.schema_field,
            tags=self.tags,
            routes=self.routes,
            nodes=self.nodes,
            links=self.links,
            node_set=self.node_set,
        )
        renderer = Renderer(show_fields=self.show_fields, module_color=self.module_color, schema=self.schema)
        return renderer.render_dot(_tags, _routes, _nodes, _links)
    
    def render_brief_dot(self, module_prefix: str | None = None):
        _tags, _routes, _nodes, _links = filter_subgraph(
            module_prefix=module_prefix,
            tags=self.tags,
            routes=self.routes,
            nodes=self.nodes,
            links=self.links,
        )
        renderer = Renderer(show_fields=self.show_fields, module_color=self.module_color, schema=None)
        return renderer.render_dot(_tags, _routes, _nodes, _links)