Changes
=======

1.6.0
-----

- **resolve many**: the new methods `resolve_many` and `resolve_many_lazy` gives you the possibility to resolve multiple objects depending on their class.
- **alias names**: you can provide a list of alias names within the object configuration.
- **constructor/factory (kw)argument overridies**: resolve methods noch accepts args and kwargs that will can be used instead of args configurations.
- **register decorator**: :code:`register` can be used as decorator now.
- **use as contextmanager**: the container can be used as context manager to temporarily override settings in :code:`with` block.

1.5.2
-----

- copy settings in DIContainer.__init__.
