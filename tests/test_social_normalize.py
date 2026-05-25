import json
import unittest
from pathlib import Path

from social_normalize import (
    ScrapeContext,
    extract_records,
    primary_record_type,
    records_to_chunks,
    top_level_metadata,
)
from main import serialize_social

FIXTURES = Path(__file__).parent / "fixtures"


class LinkedInProfileNormalizeTest(unittest.TestCase):
    def setUp(self):
        raw = json.loads((FIXTURES / "linkedin_profile.json").read_text())
        self.ctx = ScrapeContext(
            platform="linkedin",
            scraper_type="profiles",
            request_url="https://www.linkedin.com/in/jane-doe",
            raw=raw,
        )

    def test_extracts_profile_experience_education_and_posts(self):
        records = extract_records(self.ctx)
        record_types = [record.record_type for record in records]
        self.assertEqual(record_types, ["profile", "experience", "education", "post", "post"])

    def test_excludes_technical_fields_from_embed_text(self):
        chunks = records_to_chunks(extract_records(self.ctx), "linkedin")
        combined = "\n".join(chunk["text"] for chunk in chunks)
        self.assertNotIn("linkedin_id", combined)
        self.assertNotIn("followers", combined)
        self.assertNotIn("avatar", combined)
        self.assertNotIn("https://", combined)

    def test_chunk_metadata(self):
        chunks = records_to_chunks(extract_records(self.ctx), "linkedin")
        profile_chunk = chunks[0]
        self.assertEqual(profile_chunk["metadata"]["content_type"], "linkedin_record")
        self.assertEqual(profile_chunk["metadata"]["record_type"], "profile")
        self.assertEqual(profile_chunk["metadata"]["chunk_index"], 0)

        post_chunk = next(c for c in chunks if c["metadata"].get("parent_field") == "posts")
        self.assertEqual(post_chunk["metadata"]["post_index"], 0)
        self.assertEqual(post_chunk["metadata"]["urn"], "urn:li:activity:1")

    def test_serialize_social_response_shape(self):
        response = serialize_social(self.ctx)
        self.assertEqual(response["url"], self.ctx.request_url)
        self.assertEqual(response["platform"], "linkedin")
        self.assertEqual(response["record_type"], "profile")
        self.assertEqual(response["metadata"], {"title": "Jane Doe"})
        self.assertIs(response["raw"], self.ctx.raw)
        self.assertTrue(response["chunks"])


class FacebookListNormalizeTest(unittest.TestCase):
    def test_handles_list_payload(self):
        ctx = ScrapeContext(
            platform="facebook",
            scraper_type="posts_by_profile",
            request_url="https://www.facebook.com/example",
            raw=[
                {"text": "Hello world", "url": "https://www.facebook.com/post/1"},
                {"content": "Second post"},
            ],
        )
        records = extract_records(ctx)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].record_type, "post")
        self.assertEqual(primary_record_type(ctx), "post")
        self.assertEqual(top_level_metadata(records, ctx), {})


if __name__ == "__main__":
    unittest.main()
