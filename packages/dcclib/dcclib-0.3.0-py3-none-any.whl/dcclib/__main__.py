try:
    from dcclib_cli.cli import cli

    cli()
except ImportError:
    print("dcclib cli is not installed. Please install it with 'pip install dcclib[cli]'.")
