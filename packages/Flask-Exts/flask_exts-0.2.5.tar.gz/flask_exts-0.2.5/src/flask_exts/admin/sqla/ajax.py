from sqlalchemy import or_, and_, cast, text
from sqlalchemy.types import String
from ...datastore.sqla import db
from ..model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE
from ...utils.sqla import (
    get_primary_key,
    has_multiple_pks,
    is_relationship,
    is_association_proxy,
)


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name, model, session=None, **options):
        """
        Constructor.

        :param fields:
            Fields to run query against
        :param filters:
            Additional filters to apply to the loader
        """
        super().__init__(name, options)

        # set db.session as default session
        self.session = session if session is not None else db.session
        
        self.model = model
        self.fields = options.get("fields")
        self.order_by = options.get("order_by")
        self.filters = options.get("filters")

        if not self.fields:
            raise ValueError(
                "AJAX loading requires `fields` to be specified for %s.%s"
                % (model, self.name)
            )

        self._cached_fields = self._process_fields()

        if has_multiple_pks(model):
            raise NotImplementedError(
                "Current does not support multi-pk AJAX model loading."
            )

        self.pk = get_primary_key(model)

    def _process_fields(self):
        remote_fields = []

        for field in self.fields:
            if isinstance(field, str):
                attr = getattr(self.model, field, None)

                if not attr:
                    raise ValueError("%s.%s does not exist." % (self.model, field))

                remote_fields.append(attr)
            else:
                # TODO: Figure out if it is valid SQLAlchemy property?
                remote_fields.append(field)

        return remote_fields

    def format(self, model):
        if not model:
            return None

        return getattr(model, self.pk), str(model)

    def get_query(self):
        return self.session.query(self.model)

    def get_one(self, pk):
        # prevent autoflush from occuring during populate_obj
        with self.session.no_autoflush:
            return self.session.get(self.model, pk)

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.get_query()

        # debug
        # for field in self._cached_fields:
        #     if is_association_proxy(field):
        #         a = field.ilike(u'%%%s%%' % term)
        #     else:
        #         a = cast(field, String).ilike(u'%%%s%%' % term)
        if term:
            # no type casting to string if a ColumnAssociationProxyInstance is given
            filters = (
                (
                    field.ilike("%%%s%%" % term)
                    if is_association_proxy(field)
                    else cast(field, String).ilike("%%%s%%" % term)
                )
                for field in self._cached_fields
            )
            query = query.filter(or_(*filters))

        if self.filters:
            filters = [
                text("%s.%s" % (self.model.__tablename__.lower(), value))
                for value in self.filters
            ]
            query = query.filter(and_(*filters))

        if self.order_by:
            query = query.order_by(self.order_by)

        return query.offset(offset).limit(limit).all()


def create_ajax_loader(model, session, name, field_name, options):
    attr = getattr(model, field_name, None)

    if attr is None:
        raise ValueError("Model %s does not have field %s." % (model, field_name))

    if not is_relationship(attr) and not is_association_proxy(attr):
        raise ValueError("%s.%s is not a relation." % (model, field_name))

    if is_association_proxy(attr):
        attr = attr.remote_attr

    remote_model = attr.prop.mapper.class_
    return QueryAjaxModelLoader(name, remote_model, session, **options)
