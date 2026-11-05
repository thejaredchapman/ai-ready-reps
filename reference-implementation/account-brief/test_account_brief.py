import copy
import socket
import unittest

import account_brief as ab

PUBLIC = lambda host, port, **kw: [(2, 1, 6, "", ("93.184.216.34", 443))]
PRIVATE = lambda host, port, **kw: [(2, 1, 6, "", ("10.0.0.5", 443))]
PAGE = """<html><head><title>x</title></head><body><nav>Menu Home</nav>
<p>Acme Robotics is a leading robotics company. We build warehouse picking robots for retailers. Contact jane.doe@acme.example or +1 (555) 123-4567 today.</p>
<p>Founded in 2011, Acme has 450 employees across 6 offices. Acme announced a new partnership with Northwind Logistics in September.</p>
<script>var secret = "We build hidden things in scripts.";</script></body></html>"""


def pages():
    return ab.collect(["https://acme.example/about"], fetch=lambda u: PAGE, robots=lambda u: True, resolver=PUBLIC)


class PublicOnly(unittest.TestCase):
    def test_rejects_http_credentials_ports_and_internal_hosts(self):
        for u in ["http://acme.example", "https://user:pw@acme.example", "https://acme.example:8443/x", "https://intranet", "https://crm.corp.internal/x"]:
            with self.assertRaises(ab.RefusedError, msg=u):
                ab.check_public_url(u, PUBLIC)

    def test_rejects_private_address(self):
        with self.assertRaises(ab.RefusedError):
            ab.check_public_url("https://acme.example", PRIVATE)

    def test_emails_and_phones_removed(self):
        t = pages()[0]["text"]
        self.assertNotIn("jane.doe", t)
        self.assertNotIn("555", t)

    def test_scripts_and_nav_ignored(self):
        t = pages()[0]["text"]
        self.assertNotIn("hidden things", t)
        self.assertNotIn("Menu Home", t)

    def test_robots_disallow_means_no_fetch(self):
        called = []
        got = ab.collect(["https://acme.example/a"], fetch=lambda u: called.append(u) or PAGE, robots=lambda u: False, resolver=PUBLIC)
        self.assertEqual(got, [])
        self.assertEqual(called, [])

    def test_page_limit(self):
        with self.assertRaises(ab.RefusedError):
            ab.collect(["https://a.example/%d" % i for i in range(ab.MAX_PAGES + 1)], fetch=lambda u: PAGE, robots=lambda u: True, resolver=PUBLIC)


class Cited(unittest.TestCase):
    def test_every_claim_has_url_and_is_in_the_page(self):
        b = ab.build_brief("Acme", pages())
        self.assertGreaterEqual(len(b["claims"]), 2)
        text = pages()[0]["text"]
        for c in b["claims"]:
            self.assertTrue(c["source_url"].startswith("https://"))
            self.assertIn(c["text"], text)

    def test_checker_drops_invented_or_uncited_claims(self):
        pg = pages()
        fake = [{"topic": "x", "text": "Acme raised $200 million.", "source_url": pg[0]["url"]},
                {"topic": "x", "text": "Acme has 450 employees across 6 offices.", "source_url": None}]
        kept, dropped = ab.verify_claims(fake, pg)
        self.assertEqual((kept, len(dropped)), ([], 2))


class Approval(unittest.TestCase):
    def setUp(self):
        self.b = ab.build_brief("Acme", pages())

    def test_unapproved_cannot_export(self):
        with self.assertRaises(ab.RefusedError):
            ab.export_markdown(self.b)

    def test_wrong_confirmation_refused(self):
        with self.assertRaises(ab.RefusedError):
            ab.approve(self.b, "Pat", "yes")
        with self.assertRaises(ab.RefusedError):
            ab.approve(self.b, "", "APPROVE")

    def test_approved_exports_with_citations(self):
        md = ab.export_markdown(ab.approve(self.b, "Pat Rep", "APPROVE"))
        self.assertIn("Approved by Pat Rep", md)
        self.assertIn("[1]", md)
        self.assertIn("https://acme.example/about", md)

    def test_edit_after_approval_blocks_export(self):
        b = ab.approve(self.b, "Pat Rep", "APPROVE")
        b = copy.deepcopy(b)
        b["claims"][0]["text"] = "Acme is the world's best company."
        with self.assertRaises(ab.RefusedError):
            ab.export_markdown(b)

    def test_edit_before_approval_blocks_approval(self):
        self.b["claims"][0]["text"] = "Changed."
        with self.assertRaises(ab.RefusedError):
            ab.approve(self.b, "Pat", "APPROVE")


class ReadOnly(unittest.TestCase):
    def test_only_get_in_network_code(self):
        src = open(ab.__file__).read()
        for verb in ("POST", "PUT", "DELETE", "PATCH", "smtplib", "sendmail"):
            self.assertNotIn(verb, src.replace("Raised when", ""), verb)


if __name__ == "__main__":
    unittest.main()
