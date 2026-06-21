import unittest

from validate_projects import validate_projects, ValidationError


def base_project():
    return {
        "slug": "demo",
        "subdomain": "demo.easyleads.es",
        "website": "https://demo.example.com",
        "name": "Demo",
        "tagline": "Tagline de prueba",
        "description": "desc",
        "nap": {
            "streetAddress": "Calle 1",
            "addressLocality": "Bilbao",
            "postalCode": "48000",
            "addressCountry": "ES",
            "telephone": "+34 600 00 00 00",
        },
        "sameAs": ["https://example.com"],
    }


class ValidateProjectsTest(unittest.TestCase):
    def test_valid_project_list_passes(self):
        self.assertTrue(validate_projects([base_project()]))

    def test_empty_list_fails(self):
        with self.assertRaises(ValidationError):
            validate_projects([])

    def test_missing_nap_field_fails(self):
        project = base_project()
        del project["nap"]["telephone"]
        with self.assertRaises(ValidationError):
            validate_projects([project])

    def test_missing_website_fails(self):
        project = base_project()
        del project["website"]
        with self.assertRaises(ValidationError):
            validate_projects([project])

    def test_missing_tagline_fails(self):
        project = base_project()
        del project["tagline"]
        with self.assertRaises(ValidationError):
            validate_projects([project])

    def test_duplicate_slug_fails(self):
        with self.assertRaises(ValidationError):
            validate_projects([base_project(), base_project()])

    def test_invalid_same_as_url_fails(self):
        project = base_project()
        project["sameAs"] = ["not-a-url"]
        with self.assertRaises(ValidationError):
            validate_projects([project])


if __name__ == "__main__":
    unittest.main()
