"""Database utilities for Django.

This module provides utility functions for working with Django models,
including hashing, topological sorting, and database operations.
These utilities help with efficient and safe database interactions.
"""

from datetime import datetime
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, Any, Self

from django.db import connection
from django.db.models import DateTimeField, Field, Model
from django.db.models.fields.related import ForeignKey, ForeignObjectRel
from django.forms.models import model_to_dict
from winipedia_utils.logging.logger import get_logger

if TYPE_CHECKING:
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.db.models.options import Options

logger = get_logger(__name__)


def get_model_meta(model: type[Model]) -> "Options[Model]":
    """Get the Django model metadata options object.

    Retrieves the _meta attribute from a Django model class, which contains
    metadata about the model including field definitions, table name, and
    other model configuration options. This is a convenience wrapper around
    accessing the private _meta attribute directly.

    Args:
        model (type[Model]): The Django model class to get metadata from.

    Returns:
        Options[Model]: The model's metadata options object containing
            field definitions, table information, and other model configuration.

    Example:
        >>> from django.contrib.auth.models import User
        >>> meta = get_model_meta(User)
        >>> meta.db_table
        'auth_user'
        >>> len(meta.get_fields())
        11
    """
    return model._meta  # noqa: SLF001


def get_fields(
    model: type[Model],
) -> "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]":
    """Get all fields from a Django model including relationships.

    Retrieves all field objects from a Django model, including regular fields,
    foreign key relationships, reverse foreign key relationships, and generic
    foreign keys. This provides a comprehensive view of all model attributes
    that can be used for introspection, validation, or bulk operations.

    Args:
        model (type[Model]): The Django model class to get fields from.

    Returns:
        list[Field | ForeignObjectRel | GenericForeignKey]: A list
            containing all field objects associated with the model, including:
            - Regular model fields (CharField, IntegerField, etc.)
            - Foreign key fields (ForeignKey, OneToOneField, etc.)
            - Reverse relationship fields (ForeignObjectRel)
            - Generic foreign key fields (GenericForeignKey)

    Example:
        >>> from django.contrib.auth.models import User
        >>> fields = get_fields(User)
        >>> field_names = [f.name for f in fields if hasattr(f, 'name')]
        >>> 'username' in field_names
        True
        >>> 'email' in field_names
        True
    """
    return get_model_meta(model).get_fields()


def get_field_names(
    fields: "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]",
) -> list[str]:
    """Get the names of all fields from a Django model including relationships.

    Retrieves the names of all field objects from a Django model, including
    regular fields, foreign key relationships, reverse foreign key relationships,
    and generic foreign keys. This provides a comprehensive view of all model
    attributes that can be used for introspection, validation, or bulk operations.

    Args:
        fields (list[Field | ForeignObjectRel | GenericForeignKey]):
            The list of field objects to get names from.

    Returns:
        list[str]: A list containing the names of all fields.

    Example:
        >>> from django.contrib.auth.models import User
        >>> fields = get_fields(User)
        >>> field_names = get_field_names(fields)
        >>> 'username' in field_names
        True
        >>> 'email' in field_names
        True
    """
    return [field.name for field in fields]


def topological_sort_models(models: list[type[Model]]) -> list[type[Model]]:
    """Sort Django models in dependency order using topological sorting.

    Analyzes foreign key relationships between Django models and returns them
    in an order where dependencies come before dependents. This ensures that
    when performing operations like bulk creation or deletion, models are
    processed in the correct order to avoid foreign key constraint violations.

    The function uses Python's graphlib.TopologicalSorter to perform the sorting
    based on ForeignKey relationships between the provided models. Only
    relationships between models in the input list are considered.

    Args:
        models (list[type[Model]]): A list of Django model classes to sort
            based on their foreign key dependencies.

    Returns:
        list[type[Model]]: The input models sorted in dependency order, where
            models that are referenced by foreign keys appear before models
            that reference them. Self-referential relationships are ignored.

    Raises:
        graphlib.CycleError: If there are circular dependencies between models
            that cannot be resolved.

    Example:
        >>> # Assuming Author model has no dependencies
        >>> # and Book model has ForeignKey to Author
        >>> models = [Book, Author]
        >>> sorted_models = topological_sort_models(models)
        >>> sorted_models
        [<class 'Author'>, <class 'Book'>]

    Note:
        - Only considers ForeignKey relationships, not other field types
        - Self-referential foreign keys are ignored to avoid self-loops
        - Only relationships between models in the input list are considered
    """
    ts: TopologicalSorter[type[Model]] = TopologicalSorter()

    for model in models:
        deps = {
            field.related_model
            for field in get_fields(model)
            if isinstance(field, ForeignKey)
            and isinstance(field.related_model, type)
            and field.related_model in models
            and field.related_model is not model
        }
        ts.add(model, *deps)

    return list(ts.static_order())


def execute_sql(
    sql: str, params: dict[str, Any] | None = None
) -> tuple[list[str], list[Any]]:
    """Execute raw SQL query and return column names with results.

    Executes a raw SQL query using Django's database connection and returns
    both the column names and the result rows. This provides a convenient
    way to run custom SQL queries while maintaining Django's database
    connection management and parameter binding for security.

    The function automatically handles cursor management and ensures proper
    cleanup of database resources. Parameters are safely bound to prevent
    SQL injection attacks.

    Args:
        sql (str): The SQL query string to execute. Can contain parameter
            placeholders that will be safely bound using the params argument.
        params (dict[str, Any] | None, optional): Dictionary of parameters
            to bind to the SQL query for safe parameter substitution.
            Defaults to None if no parameters are needed.

    Returns:
        tuple[list[str], list[Any]]: A tuple containing:
            - list[str]: Column names from the query result
            - list[Any]: List of result rows, where each row is a tuple
              of values corresponding to the column names

    Raises:
        django.db.Error: If there's a database error during query execution
        django.db.ProgrammingError: If the SQL syntax is invalid
        django.db.IntegrityError: If the query violates database constraints

    Example:
        >>> sql = "SELECT id, username FROM auth_user WHERE is_active = %(active)s"
        >>> params = {"active": True}
        >>> columns, rows = execute_sql(sql, params)
        >>> columns
        ['id', 'username']
        >>> rows[0]
        (1, 'admin')

    Note:
        - Uses Django's default database connection
        - Automatically manages cursor lifecycle
        - Parameters are safely bound to prevent SQL injection
        - Returns all results in memory - use with caution for large datasets
    """
    with connection.cursor() as cursor:
        cursor.execute(sql=sql, params=params)
        rows = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]

    return column_names, rows


def hash_model_instance(
    instance: Model,
    fields: "list[Field[Any, Any] | ForeignObjectRel | GenericForeignKey]",
) -> int:
    """Hash a model instance based on its field values.

    Generates a hash for a Django model instance by considering the values
    of its fields. This can be useful for comparing instances, especially
    when dealing with related objects or complex data structures. The hash
    is generated by recursively hashing related objects up to a specified
    depth.
    This is not very reliable, use with caution.
    Only use if working with unsafed objects or bulks, as with safed

    Args:
        instance (Model): The Django model instance to hash
        fields (list[str]): The fields to hash

    Returns:
        int: The hash value representing the instance's data

    """
    if instance.pk:
        return hash(instance.pk)

    field_names = get_field_names(fields)
    model_dict = model_to_dict(instance, fields=field_names)
    sorted_dict = dict(sorted(model_dict.items()))
    values = (type(instance), tuple(sorted_dict.items()))
    return hash(values)


class BaseModel(Model):
    """Base model for all models in the project.

    Provides common fields and methods for all models.
    """

    created_at: DateTimeField[datetime, datetime] = DateTimeField(auto_now_add=True)
    updated_at: DateTimeField[datetime, datetime] = DateTimeField(auto_now=True)

    class Meta:
        """Mark the model as abstract."""

        # abstract does not inherit in children
        abstract = True

    def __str__(self) -> str:
        """Base string representation of a model.

        Returns:
            str: The string representation of the model as all fields and their values.
        """
        fields_values = ", ".join(
            f"{field.name}={getattr(self, field.name)}"
            for field in get_fields(self.__class__)
        )
        return f"{self.__class__.__name__}({fields_values})"

    def __repr__(self) -> str:
        """Base representation of a model."""
        return str(self)

    @property
    def meta(self) -> "Options[Self]":
        """Get the meta options for the model."""
        return self._meta
