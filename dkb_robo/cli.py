# pylint: disable=c3001, e1101, r0913, w0108, w0622
""" dkb_robo cli """
from datetime import date
from pprint import pprint
import sys
import csv
import json
import tabulate
import click
import dkb_robo
sys.path.append("..")

DATE_FORMAT = "%d.%m.%Y"


@click.group()
@click.option(
    "--debug",
    "-d",
    default=False,
    help="Show additional debugging",
    is_flag=True,
    envvar="DKB_DEBUG",
)
@click.option(
    "--use-tan",
    "-t",
    default=False,
    help="dbk-robo will ask for a TAN (generated by either ChipTan or TAN2go) during login",
    is_flag=True,
    envvar="DKB_USE_TAN",
)
@click.option(
    "--username",
    "-u",
    required=True,
    type=str,
    help="username to access the dkb portal",
    envvar="DKB_USERNAME",
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    hide_input=True,
    type=str,
    help="corresponding login password",
    envvar="DKB_PASSWORD",
)
@click.option(
    "--format",
    default="pprint",
    type=click.Choice(["pprint", "table", "csv", "json"]),
    help="output format to use",
    envvar="DKB_FORMAT",
)
@click.pass_context
def main(ctx, debug, use_tan, username, password, format):  # pragma: no cover
    """ main fuunction """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["USE_TAN"] = use_tan
    ctx.obj["USERNAME"] = username
    ctx.obj["PASSWORD"] = password
    ctx.obj["FORMAT"] = _load_format(format)


@main.command()
@click.pass_context
def accounts(ctx):
    """ get list of account """
    try:
        with _login(ctx) as dkb:
            accounts_dict = dkb.account_dic
            for _, value in accounts_dict.items():
                del value["details"]
                del value["transactions"]
            ctx.obj["FORMAT"](list(accounts_dict.values()))
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
@click.option(
    "--name",
    "-n",
    type=str,
    help="Name of the account to fetch transactions for",
    envvar="DKB_TRANSACTIONS_ACCOUNT_NAME",
)
@click.option(
    "--account",
    "-a",
    type=str,
    help="Account to fetch transactions for",
    envvar="DKB_TRANSACTIONS_ACCOUNT",
)
@click.option(
    "--transaction-type",
    "-t",
    default="booked",
    type=click.Choice(["booked", "reserved"]),
    help="The type of transactions to fetch",
    envvar="DKB_TRANSACTIONS_TYPE",
)
@click.option(
    "--date-from",
    type=click.DateTime(formats=[DATE_FORMAT]),
    default=date.today().strftime(DATE_FORMAT),
)
@click.option(
    "--date-to",
    type=click.DateTime(formats=[DATE_FORMAT]),
    default=date.today().strftime(DATE_FORMAT),
)
def transactions(ctx, name, account, transaction_type, date_from, date_to):  # pragma: no cover
    """ get list of transactions """

    if name is not None and account is None:
        def account_filter(acct): return acct["name"] == name  # nopep8
    elif account is not None and name is None:
        def account_filter(acct): return acct["account"] == account
    else:
        raise click.UsageError("One of --name or --account must be provided.", ctx)

    try:
        with _login(ctx) as dkb:
            accounts_dict = dkb.account_dic
            filtered_accounts = [
                acct for acct in accounts_dict.values() if account_filter(acct)
            ]
            if len(filtered_accounts) == 0:
                click.echo(f"No account found matching '{name or account}'", err=True)
                return
            the_account = filtered_accounts[0]
            transactions_list = dkb.get_transactions(
                the_account["transactions"],
                the_account["type"],
                date_from.strftime(DATE_FORMAT),
                date_to.strftime(DATE_FORMAT),
                transaction_type=transaction_type,
            )
            ctx.obj["FORMAT"](transactions_list)

    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
def last_login(ctx):
    """ get last login """
    try:
        with _login(ctx) as dkb:
            ctx.obj["FORMAT"]([{"last_login": dkb.last_login}])
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
def credit_limits(ctx):
    """ get limits """
    try:
        with _login(ctx) as dkb:
            limits = dkb.get_credit_limits()
            limits = [{"account": k, "limit": v} for k, v in limits.items()]
            ctx.obj["FORMAT"](limits)
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
def standing_orders(ctx):
    """ get standing orders """
    try:
        with _login(ctx) as dkb:
            ctx.obj["FORMAT"](dkb.get_standing_orders())
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


def _load_format(output_format):
    """ select output format based on cli option """
    if output_format == "pprint":
        return lambda data: pprint(data)

    if output_format == "table":
        return lambda data: click.echo(
            tabulate.tabulate(data, headers="keys", tablefmt="grid")
        )

    if output_format == "csv":
        def formatter(data):  # pragma: no cover
            if len(data) == 0:
                return
            writer = csv.DictWriter(sys.stdout, data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return formatter

    if output_format == "json":

        return lambda data: click.echo(json.dumps(data, indent=2))

    raise Exception(f"Unknown format: {output_format}")


def _login(ctx):
    return dkb_robo.DKBRobo(
        ctx.obj["USERNAME"], ctx.obj["PASSWORD"], ctx.obj["USE_TAN"], ctx.obj["DEBUG"]
    )
