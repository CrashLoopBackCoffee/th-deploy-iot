import pulumi as p

# Dev stack is the legacy stack
if p.get_stack() == 'dev':
    import iot.main_legacy

    iot.main_legacy.main()
else:
    import iot.main

    iot.main.main()
