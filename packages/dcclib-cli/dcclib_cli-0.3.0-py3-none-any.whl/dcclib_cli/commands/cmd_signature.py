import sys

import click
from lxml import etree

from dcclib.signature import DCCSigner, DCCVerifier

from .output import echo_err, echo_success, echo_warn


@click.group("signature", short_help="Signs and verifies DCC XML files.")
def cli():
    pass


@cli.command("sign", short_help="Signs a DCC XML file using a certificate.")
@click.argument("cert_file", metavar="CERT_PATH", type=click.File(encoding="utf-8"))
@click.argument("key_file", metavar="KEY_PATH", type=click.File(encoding="utf-8"))
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(),
    help="Path to write the output to.",
)
def apply(cert_file, key_file, xml_file, output):
    cert_content = cert_file.read()
    key_content = key_file.read()
    xml_content = xml_file.read()

    signer = DCCSigner(key_content, cert_content)

    try:
        signed_xml = signer.sign_str(xml_content)
    except Exception as e:
        click.echo(f"Could not sign XML: {e}")
        sys.exit(1)

    if output is None or output == "-":
        click.echo(signed_xml)
    else:
        with open(output, "w", encoding="utf-8") as f:
            f.write(signed_xml)
        click.echo(f"Signed XML written to {output}")


@cli.command(
    "verify",
    short_help="Verifies the signature of a DCC XML file and extracts the signed XML content.",
)
@click.argument(
    "ca_cert_file",
    metavar="CA_CERT_PATH",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(),
    help="Path to write the signed XML content to.",
)
def verify(ca_cert_file, xml_file, output):
    xml_content = xml_file.read()

    verifier = DCCVerifier(ca_cert_file)

    try:
        result = verifier.verify_str(xml_content)
    except Exception as e:
        echo_err(f"Could not verify XML: {e}")
        sys.exit(1)

    if output != "-":
        click.echo("Verification successful.")
        click.echo(f"Subject: {result.cert.subject.rfc4514_string()}")
        click.echo(f"Issuer: {result.cert.issuer.rfc4514_string()}")
        click.echo(f"Validity Period: {result.cert.not_valid_before_utc} to {result.cert.not_valid_after_utc}")
        click.echo(f"Serial Number: {result.cert.serial_number}")
        click.echo(f"Signature Algorithm: {result.cert.signature_algorithm_oid._name}")

    verified_xml_content = etree.tostring(result.signed_tree).decode("utf-8")

    if output == "-":
        click.echo(verified_xml_content)
    elif output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(verified_xml_content)
        echo_success(f"Signed XML content written to {output}")
    else:
        echo_warn(
            "The signed XML content is not guaranteed to be the same as the original XML content. Ensure that the "
            "information trusted is what was actually signed by only trusting the data returned by the `-o <xml_file>` "
            "option."
        )
