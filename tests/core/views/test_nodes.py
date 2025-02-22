import json

from django.urls import reverse

from papermerge.test import TestCase
from papermerge.core.models import (
    Folder,
    Document,
    Tag
)


class NodesViewTestCase(TestCase):

    def test_get_inboxcount_when_inbox_is_empty(self):
        """
        GET /nodes/inboxcount/ returns number of descendants of user's inbox
        folder.

        In this test user's inbox is empty.
        """
        response = self.client.get(reverse('inboxcount'))

        assert response.status_code == 200

        # user's inbox is empty
        assert response.data == {'count': 0}

    def test_get_inboxcount_with_one_item_in_inbox(self):
        """
        GET /nodes/inboxcount/ returns number of descendants of user's inbox
        folder.
        In this test user's inbox contains one single item (one folder).
        """
        Folder.objects.create(
            title='I am inside .inbox',
            user=self.user,
            parent=self.user.inbox_folder
        )
        response = self.client.get(reverse('inboxcount'))
        assert response.status_code == 200

        # user's inbox contains one item
        assert response.data == {'count': 1}

    def test_get_inboxcount_containing_recursive_items(self):
        """
        Inbox folder contains two folders:
        - My Documents
        - My Invoices

        Both My Documents and My Invoices contains another two documents:
        - My Documents
            - doc1.pdf
            - doc2.pdf
        - My Invoices
            - invoice1.pdf
            - invoice2.pdf

        In such case, inbox should show item count = 2, which corresponds to the
        two direct children of the inbox - 'My Documents' and 'My Invoices'
        """
        my_documents = Folder.objects.create(
            title='My Documents',
            user=self.user,
            parent=self.user.inbox_folder
        )
        Document.objects.create(
            title='doc1.pdf',
            user=self.user,
            parent=my_documents
        )
        Document.objects.create(
            title='doc2.pdf',
            user=self.user,
            parent=my_documents
        )
        my_invoices = Folder.objects.create(
            title='My Invoices',
            user=self.user,
            parent=self.user.inbox_folder
        )
        Document.objects.create(
            title='invoice1.pdf',
            user=self.user,
            parent=my_invoices
        )
        Document.objects.create(
            title='invoice2.pdf',
            user=self.user,
            parent=my_invoices
        )

        response = self.client.get(reverse('inboxcount'))
        assert response.status_code == 200

        # user's inbox contains one item
        assert response.data == {'count': 2}

    def test_assign_tags_to_non_tagged_folder(self):
        """
        url:
            POST /api/nodes/{N1}/tags/
        body content:
            ["paid", "important"]

        where N1 is a folder without any tag

        Expected result:
            folder N1 will have two tags assigned: 'paid' and 'important'
        """
        receipts = Folder.objects.create(
            title='Receipts',
            user=self.user,
            parent=self.user.inbox_folder
        )
        data = {
            'tags': ['paid', 'important']
        }
        url = reverse('node-tags', args=(receipts.pk, ))
        response = self.post(url, data)

        assert response.status_code == 201
        assert receipts.tags.count() == 2

    def test_assign_tags_to_tagged_folder(self):
        """
        url:
            POST /api/nodes/{N1}/tags/
        body content:
            ["paid", "important"]

        where N1 is a folder with two tags 'important' and 'unpaid' already
        assigned

        Expected result:
            folder N1 will have two tags assigned: 'paid' and 'important'.
            Tag 'unpaid' will be dissociated from the folder.
        """
        receipts = Folder.objects.create(
            title='Receipts',
            user=self.user,
            parent=self.user.inbox_folder
        )
        receipts.tags.set(
            ['unpaid', 'important'],
            tag_kwargs={"user": self.user}
        )
        data = {
            'tags': ['paid', 'important']
        }
        url = reverse('node-tags', args=(receipts.pk, ))
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 201
        assert receipts.tags.count() == 2
        all_new_tags = [tag.name for tag in receipts.tags.all()]
        # tag 'unpaid' is not attached to folder anymore
        assert set(all_new_tags) == set(['paid', 'important'])
        # model for tag 'unpaid' still exists, it was just
        # dissociated from folder 'Receipts'
        assert Tag.objects.get(name='unpaid')

    def test_append_tags_to_folder(self):
        """
        url:
            PATCH /api/nodes/{N1}/tags/
        body content:
            ["paid"]

        where N1 is a folder with already one tag attached: 'important'

        Expected result:
            folder N1 will have two tags assigned: 'paid' and 'important'
            Notice that 'paid' was appended next to 'important'.
        """
        receipts = Folder.objects.create(
            title='Receipts',
            user=self.user,
            parent=self.user.inbox_folder
        )
        receipts.tags.set(
            ['important'],
            tag_kwargs={"user": self.user}
        )
        data = {
            'tags': ['paid']
        }
        url = reverse('node-tags', args=(receipts.pk, ))
        response = self.client.patch(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        assert receipts.tags.count() == 2
        all_new_tags = [tag.name for tag in receipts.tags.all()]

        assert set(all_new_tags) == set(['paid', 'important'])

    def test_remove_tags_from_folder(self):
        """
        url:
            DELETE /api/nodes/{N1}/tags/
        body content:
            ["important"]

        where N1 is a folder with four tags 'important', 'paid', 'receipt',
        'bakery'

        Expected result:
            folder N1 will have three tags assigned: 'paid', 'bakery', 'receipt'
        """
        receipts = Folder.objects.create(
            title='Receipts',
            user=self.user,
            parent=self.user.inbox_folder
        )
        receipts.tags.set(
            ['important', 'paid', 'receipt', 'bakery'],
            tag_kwargs={"user": self.user}
        )
        data = {
            'tags': ['important']
        }
        url = reverse('node-tags', args=(receipts.pk, ))
        response = self.client.delete(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 204
        assert receipts.tags.count() == 3
        all_new_tags = [tag.name for tag in receipts.tags.all()]
        assert set(all_new_tags) == set(['paid', 'bakery', 'receipt'])

    def test_home_with_two_tagged_nodes(self):
        """
        Create two tagged nodes (one folder and one document) in user's home.
        Retrieve user's home content and check that tags
        were included in response as well.
        """
        folder = Folder.objects.create(
            title='folder',
            user=self.user,
            parent=self.user.home_folder
        )
        folder.tags.set(
            ['folder_a', 'folder_b'],
            tag_kwargs={"user": self.user}
        )
        doc = Document.objects.create(
            title='doc.pdf',
            user=self.user,
            parent=self.user.home_folder
        )
        doc.tags.set(
            ['doc_a', 'doc_b'],
            tag_kwargs={"user": self.user}
        )
        home = self.user.home_folder
        url = reverse('node-detail', args=(home.pk, ))

        response = self.client.get(url)
        assert response.status_code == 200
        results = response.data['results']
        assert len(results) == 2  # there are two folders

        doc_tag_names = [tag['name'] for tag in results[0]['tags']]
        folder_tag_names = [tag['name'] for tag in results[1]['tags']]

        assert set(['doc_a', 'doc_b']) == set(doc_tag_names)
        assert set(['folder_a', 'folder_b']) == set(folder_tag_names)

    def test_nodes_move(self):
        doc = Document.objects.create(
            title='doc.pdf',
            user=self.user,
            parent=self.user.inbox_folder
        )

        url = reverse('nodes-move')
        data = {
            'nodes': [
                {'id': str(doc.id)}
            ],
            'target_parent': {
                'id': str(self.user.home_folder.id)
            }
        }

        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200, response.data

    def test_create_document(self):
        """
        When 'lang' attribute is not specified during document creation
        it is set from user preferences['ocr_language']
        """
        assert Document.objects.count() == 0

        json_data = {
            "data": {
                "type": "documents",
                "attributes": {
                    # "lang" attribute is not set
                    "title": "doc1.pdf"
                },
                "relationships": {
                    "parent": {
                        "data": {
                            "type": "folders",
                            "id": str(self.user.home_folder.pk)
                        }
                    }
                }
            }
        }

        url = reverse('node-list')
        response = self.post(url, json_data, type="vnd.api")

        assert response.status_code == 201
        assert Document.objects.count() == 1

        doc = Document.objects.first()
        assert doc.lang == self.user.preferences['ocr__language']

    def test_two_folders_with_same_title_under_same_parent(self):
        """It should not be possible to create two folders with
        same (parent, title) pair i.e. we cannot have folders with same
        title under same parent
        """
        json_data = {
            "data": {
                "type": "folders",
                "attributes": {
                    "title": "My Documents"
                },
                "relationships": {
                    "parent": {
                        "data": {
                            "type": "folders",
                            "id": str(self.user.home_folder.pk)
                        }
                    }
                }
            }
        }

        url = reverse('node-list')
        # Create first folder 'My documents' (inside home folder)
        response = self.post(url, json_data, type="vnd.api")
        assert response.status_code == 201

        # Create second folder 'My Documents' also inside home folder
        response = self.post(url, json_data, type="vnd.api")
        assert response.status_code == 400
        assert response.data[0]['code'] == 'unique'

    def test_two_folders_with_same_title_under_different_parents(self):
        """It should be possible to create two folders with
        same if they are under different parents.
        """
        json_data = {
            "data": {
                "type": "folders",
                "attributes": {
                    "title": "My Documents"
                },
                "relationships": {
                    "parent": {
                        "data": {
                            "type": "folders",
                            "id": str(self.user.home_folder.pk)
                        }
                    }
                }
            }
        }

        url = reverse('node-list')
        # Create first folder 'My documents' (inside home folder)
        response = self.post(url, json_data, type="vnd.api")
        assert response.status_code == 201

        # Create second folder 'My Documents' also inside home folder
        json_data = {
            "data": {
                "type": "folders",
                "attributes": {
                    "title": "My Documents"
                },
                "relationships": {
                    "parent": {
                        "data": {
                            "type": "folders",
                            "id": str(self.user.inbox_folder.pk)
                        }
                    }
                }
            }
        }
        # create folder 'My Documents' in Inbox
        response = self.post(url, json_data, type="vnd.api")
        assert response.status_code == 201

    def test_two_documents_with_same_title_under_same_parent(self):
        """It should not be possible to create two documents with
        same (parent, title) pair i.e. we cannot have documents with same
        title under same parent
        """
        json_data = {
            "data": {
                "type": "documents",
                "attributes": {
                    "title": "invoice.pdf",
                    "lang": "deu"
                },
                "relationships": {
                    "parent": {
                        "data": {
                            "type": "folders",
                            "id": str(self.user.home_folder.pk)
                        }
                    }
                }
            }
        }

        url = reverse('node-list')
        # Create first folder 'My documents' (inside home folder)
        response = self.post(url, json_data, type="vnd.api")
        assert response.status_code == 201

        # Create second folder 'My Documents' also inside home folder
        response = self.post(url, json_data, type="vnd.api")
        assert response.status_code == 400
        assert response.data[0]['code'] == 'unique'
