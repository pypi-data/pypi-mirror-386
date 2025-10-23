from cryptography import x509
from cryptography.hazmat.backends import default_backend
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods

from ..constants import NAMESPACES


class DCCVerifyResult:
    """
    Class to represent the result of a verification.
    """

    def __init__(
        self,
        signed_tree: etree.Element,
        signature_tree: etree.Element,
        cert: x509.Certificate,
    ):
        """
        Create a new DCCVerifyResult.
        @param signed_tree: the tree of the signed XML
        @param signature_tree: the tree of the signature
        @param cert: the certificate used for signing
        """
        self.signed_tree = signed_tree
        self.signature_tree = signature_tree
        self.cert = cert


class DCCSigner:
    """
    Class to sign XML files with a private key and certificate.
    """

    def __init__(self, key: str, cert: str):
        """
        Create a new DCCSigner.
        @param key: the private key
        @param cert: the full certificate chain, including intermediate certificates, in PEM format.
        """
        self.key = key
        self.cert = cert

    def sign_tree(self, xml_tree: etree.Element) -> etree.Element:
        """
        Sign an XML tree.
        @param xml_tree: the XML tree to sign
        @return: the signed XML tree
        @raise Exception: if the XML could not be signed
        """
        signer = XMLSigner(method=methods.enveloped)

        return signer.sign(xml_tree, key=self.key, cert=self.cert)

    def sign_path(self, path: str) -> etree.Element:
        """
        Sign an XML file.
        @param path: the path to the XML file
        @return: the signed XML tree
        @raise Exception: if the XML could not be signed
        """
        parser = etree.XMLParser()
        tree = etree.parse(path, parser=parser)
        return self.sign_tree(tree.getroot())

    def sign_str(self, xml: str) -> etree.Element:
        """
        Sign an XML string.
        @param xml: the XML string to sign
        @return: the signed XML string
        @raise Exception: if the XML could not be signed
        """
        xml_tree = etree.fromstring(xml.encode("utf-8"))
        return etree.tostring(self.sign_tree(xml_tree)).decode("utf-8")


class DCCVerifier:
    """
    Class to verify XML files.
    """

    def __init__(self, ca_pem_file: str = None):
        """
        Create a new DCCVerifier.
        @param ca_pem_file: the path to the CA PEM file
        @warning: by default, the systems CA certificates are used. See here: https://xml-security.github.io/signxml#verifying-saml-assertions
        """
        self.ca_pem_file = ca_pem_file
        self.verifier = XMLVerifier()

    def verify_tree(self, xml_tree: etree.Element) -> DCCVerifyResult:
        """
        Verify an XML tree.
        @param xml_tree: the XML tree to verify
        @return: the verification result
        @raise Exception: if the XML could not be verified
        @warning: signxml is used to verify the XML. See the security recommendations here: https://xml-security.github.io/signxml/#signxml.XMLVerifier
        """
        result = self.verifier.verify(xml_tree, ca_pem_file=self.ca_pem_file)
        pem_data = result.signature_xml.find(".//ds:X509Certificate", namespaces=NAMESPACES).text

        if not pem_data:
            raise ValueError("No certificate found in signature.")

        pem_data = pem_data.strip()
        pem_data = (
            pem_data
            if pem_data.startswith("-----BEGIN CERTIFICATE-----") and pem_data.endswith("-----END CERTIFICATE-----")
            else f"-----BEGIN CERTIFICATE-----\n{pem_data.strip()}\n-----END CERTIFICATE-----"
        )

        cert = x509.load_pem_x509_certificate(pem_data.encode("utf-8"), default_backend())

        return DCCVerifyResult(
            signed_tree=result.signed_xml,
            signature_tree=result.signature_xml,
            cert=cert,
        )

    def verify_path(self, path: str):
        """
        Verify an XML file.
        @param path: the path to the XML file
        @return: the verification result
        @raise Exception: if the XML could not be verified
        @warning: signxml is used to verify the XML. See the security recommendations here: https://xml-security.github.io/signxml/#signxml.XMLVerifier
        """
        parser = etree.XMLParser()
        tree = etree.parse(path, parser=parser)
        return self.verify_tree(tree.getroot())

    def verify_str(self, xml: str):
        """
        Verify an XML string.
        @param xml: the XML string to verify
        @return: the verification result
        @raise Exception: if the XML could not be verified
        @warning: signxml is used to verify the XML. See the security recommendations here: https://xml-security.github.io/signxml/#signxml.XMLVerifier
        """
        root = etree.fromstring(xml.encode("utf-8"))
        return self.verify_tree(root)
