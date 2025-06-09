import rules


@rules.predicate
def is_administrator(user, obj):
    return getattr(user, "is_administrator", False)


rules.add_perm("person.is_administrator", is_administrator)
