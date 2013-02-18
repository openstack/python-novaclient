import os
import re
import sys
import uuid

import prettytable

from novaclient import exceptions


def arg(*args, **kwargs):
    """Decorator for CLI args."""
    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func
    return _decorator


def env(*args, **kwargs):
    """
    returns the first environment variable set
    if none are non-empty, defaults to '' or keyword arg default
    """
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get('default', '')


def add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(f, 'arguments'):
        f.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in f.arguments:
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        f.arguments.insert(0, (args, kwargs))


def bool_from_str(val):
    """Convert a string representation of a bool into a bool value"""

    if not val:
        return False
    try:
        return bool(int(val))
    except ValueError:
        if val.lower() in ['true', 'yes', 'y']:
            return True
        if val.lower() in ['false', 'no', 'n']:
            return False
        raise


def add_resource_manager_extra_kwargs_hook(f, hook):
    """Adds hook to bind CLI arguments to ResourceManager calls.

    The `do_foo` calls in shell.py will receive CLI args and then in turn pass
    them through to the ResourceManager. Before passing through the args, the
    hooks registered here will be called, giving us a chance to add extra
    kwargs (taken from the command-line) to what's passed to the
    ResourceManager.
    """
    if not hasattr(f, 'resource_manager_kwargs_hooks'):
        f.resource_manager_kwargs_hooks = []

    names = [h.__name__ for h in f.resource_manager_kwargs_hooks]
    if hook.__name__ not in names:
        f.resource_manager_kwargs_hooks.append(hook)


def get_resource_manager_extra_kwargs(f, args, allow_conflicts=False):
    """Return extra_kwargs by calling resource manager kwargs hooks."""
    hooks = getattr(f, "resource_manager_kwargs_hooks", [])
    extra_kwargs = {}
    for hook in hooks:
        hook_name = hook.__name__
        hook_kwargs = hook(args)

        conflicting_keys = set(hook_kwargs.keys()) & set(extra_kwargs.keys())
        if conflicting_keys and not allow_conflicts:
            raise Exception("Hook '%(hook_name)s' is attempting to redefine"
                            " attributes '%(conflicting_keys)s'" % locals())

        extra_kwargs.update(hook_kwargs)

    return extra_kwargs


def unauthenticated(f):
    """
    Adds 'unauthenticated' attribute to decorated function.
    Usage:
        @unauthenticated
        def mymethod(f):
            ...
    """
    f.unauthenticated = True
    return f


def isunauthenticated(f):
    """
    Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator. Returns True if decorator is
    set to True, False otherwise.
    """
    return getattr(f, 'unauthenticated', False)


def service_type(stype):
    """
    Adds 'service_type' attribute to decorated function.
    Usage:
        @service_type('volume')
        def mymethod(f):
            ...
    """
    def inner(f):
        f.service_type = stype
        return f
    return inner


def get_service_type(f):
    """
    Retrieves service type from function
    """
    return getattr(f, 'service_type', None)


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, formatters={}, sortby_index=0):
    if sortby_index == None:
        sortby = None
    else:
        sortby = fields[sortby_index]
    mixed_case_fields = ['serverId']
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
    pt.align = 'l'

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                if field in mixed_case_fields:
                    field_name = field.replace(' ', '_')
                else:
                    field_name = field.lower().replace(' ', '_')
                data = getattr(o, field_name, '')
                row.append(data)
        pt.add_row(row)

    if sortby is not None:
        print(pt.get_string(sortby=sortby))
    else:
        print(pt.get_string())


def print_dict(d, dict_property="Property"):
    pt = prettytable.PrettyTable([dict_property, 'Value'], caching=False)
    pt.align = 'l'
    for k, v in d.iteritems():
        # convert dict to str to check length
        if isinstance(v, dict):
            v = str(v)
        # if value has a newline, add in multiple rows
        # e.g. fault with stacktrace
        if v and isinstance(v, basestring) and r'\n' in v:
            lines = v.strip().split(r'\n')
            col1 = k
            for line in lines:
                pt.add_row([col1, line])
                col1 = ''
        else:
            pt.add_row([k, v])
    print(pt.get_string())


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        is_intid = isinstance(name_or_id, int) or name_or_id.isdigit()
    except AttributeError:
        is_intid = False

    if is_intid:
        try:
            return manager.get(int(name_or_id))
        except exceptions.NotFound:
            pass

    # now try to get entity as uuid
    try:
        uuid.UUID(str(name_or_id))
        return manager.get(name_or_id)
    except (ValueError, exceptions.NotFound):
        pass

    # for str id which is not uuid (for Flavor search currently)
    if getattr(manager, 'is_alphanum_id_allowed', False):
        try:
            return manager.get(name_or_id)
        except exceptions.NotFound:
            pass

    try:
        try:
            return manager.find(human_id=name_or_id)
        except exceptions.NotFound:
            pass

        # finally try to find entity by name
        try:
            resource = getattr(manager, 'resource_class', None)
            name_attr = resource.NAME_ATTR if resource else 'name'
            kwargs = {name_attr: name_or_id}
            return manager.find(**kwargs)
        except exceptions.NotFound:
            msg = "No %s with a name or ID of '%s' exists." % \
                (manager.resource_class.__name__.lower(), name_or_id)
            raise exceptions.CommandError(msg)
    except exceptions.NoUniqueMatch:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exceptions.CommandError(msg)


def _format_servers_list_networks(server):
    output = []
    for (network, addresses) in server.networks.items():
        if len(addresses) == 0:
            continue
        addresses_csv = ', '.join(addresses)
        group = "%s=%s" % (network, addresses_csv)
        output.append(group)

    return '; '.join(output)


def _format_security_groups(groups):
    return ', '.join(group['name'] for group in groups)


def _format_field_name(attr):
    """Format an object attribute in a human-friendly way."""
    # Split at ':' and leave the extension name as-is.
    parts = attr.rsplit(':', 1)
    name = parts[-1].replace('_', ' ')
    # Don't title() on mixed case
    if name.isupper() or name.islower():
        name = name.title()
    parts[-1] = name
    return ': '.join(parts)


def _make_field_formatter(attr, filters=None):
    """
    Given an object attribute, return a formatted field name and a
    formatter suitable for passing to print_list.

    Optionally pass a dict mapping attribute names to a function. The function
    will be passed the value of the attribute and should return the string to
    display.
    """
    filter_ = None
    if filters:
        filter_ = filters.get(attr)

    def get_field(obj):
        field = getattr(obj, attr, '')
        if field and filter_:
            field = filter_(field)
        return field

    name = _format_field_name(attr)
    formatter = get_field
    return name, formatter


class HookableMixin(object):
    """Mixin so classes can register and run hooks."""
    _hooks_map = {}

    @classmethod
    def add_hook(cls, hook_type, hook_func):
        if hook_type not in cls._hooks_map:
            cls._hooks_map[hook_type] = []

        cls._hooks_map[hook_type].append(hook_func)

    @classmethod
    def run_hooks(cls, hook_type, *args, **kwargs):
        hook_funcs = cls._hooks_map.get(hook_type) or []
        for hook_func in hook_funcs:
            hook_func(*args, **kwargs)


def safe_issubclass(*args):
    """Like issubclass, but will just return False if not a class."""

    try:
        if issubclass(*args):
            return True
    except TypeError:
        pass

    return False


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    return getattr(sys.modules[mod_str], class_str)

_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


# http://code.activestate.com/recipes/
#   577257-slugify-make-a-string-usable-in-a-url-or-filename/
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)


def is_uuid_like(val):
    """
    The UUID which doesn't contain hyphens or 'A-F' is allowed.
    """
    try:
        if uuid.UUID(val) and val.isalnum() and val.islower():
            return True
        else:
            return False
    except (TypeError, ValueError, AttributeError):
        return False
