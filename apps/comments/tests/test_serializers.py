from django.test import TestCase
from apps.comments.serializers import CommentSerializer


class CommentSerializersTest(TestCase):
    def test_comment_serializer_blank_content_invalid(self):
        data = {'content': '   '}
        serializer = CommentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_comment_serializer_valid(self):
        data = {'content': 'Great task implementation!'}
        serializer = CommentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
