from django.urls import include, path
from .views import access as access_views
from .views import tags as tags_views
from .views import api as api_views
from .views import documents as doc_views
from .views import nodes as node_views
from .views import metadata as metadata_views
from .views import users as users_views
from .views import automates as automate_views
from .views import langs as langs_views
from .views import folder

document_patterns = [
    path(
        '<int:id>/preview/page/<int:page>',
        doc_views.preview,
        name="preview"
    ),
    path(
        '<int:id>/<int:document_version>/text/page/<int:page_number>',
        doc_views.text_view,
        name="text_view"
    ),
    path(
        'usersettings/<str:option>/<str:value>',
        doc_views.usersettings,
        name="usersettings"
    ),
]

app_name = 'core'

urlpatterns = [
    path(
        'viewer/document/<int:doc_id>/',
        doc_views.document_view,
        name="document"
    ),
    path(
        'viewer/document/<int:doc_id>/page/<int:page_num>/',
        doc_views.page_view,
        name="page"
    ),
    path(
        'folder/',
        node_views.folder_view,
        name="folder"
    ),
    path(
        'folder/<int:node_id>/',
        node_views.folder_view,
        name="folder"
    ),
    path(
        'folder/add/', folder.FolderCreateView.as_view(), name='folder-add'
    ),
    path('ocr-langs/', langs_views.langs_view, name="langs_view"),
    path('document/add/', doc_views.upload, name="upload"),
    path('breadcrumb/', node_views.breadcrumb_view, name="breadcrumb"),
    path(
        'breadcrumb/<int:parent_id>/',
        node_views.breadcrumb_view,
        name="breadcrumb"
    ),
    path('node/<int:node_id>', node_views.node_view, name="node"),
    # Node can be a document or a folder
    # Downloading entire folder by selecting it - makes perfect sense
    path(
        'node/v<int:version>/<int:id>/download/',
        node_views.node_download,
        name="node_versioned_download"
    ),
    path(
        'node/<int:id>/download/',
        node_views.node_download,
        name="node_download"
    ),
    path(
        'node/by/title/<str:title>', node_views.node_by_title_view,
        name="node_by_title"
    ),
    path('nodes/', node_views.nodes_view, name="nodes"),
    # when user selected multiple documents and folders for download
    path('nodes/download/', node_views.nodes_download, name="nodes_download"),
    path(
        'node/<int:id>/access', access_views.access_view, name="access"
    ),
    path(
        'node/<int:node_id>/tags/', tags_views.tags_view, name="tags"
    ),
    path(
        'nodes/tags/', tags_views.nodes_tags_view, name="nodes_tags"
    ),
    path(
        'alltags/', tags_views.alltags_view, name="alltags"
    ),
    path(
        'metadata/<model>/<int:id>', metadata_views.metadata, name="metadata"
    ),
    path(
        'usergroups', access_views.user_or_groups, name="user_or_groups"
    ),
    path(
        'rename-node/<int:id>',
        doc_views.rename_node,
        name='rename_node'
    ),
    path(
        'cut-node/',
        doc_views.cut_node,
        name='cut_node'
    ),
    path(
        'paste-node/',
        doc_views.paste_node,
        name='paste_node'
    ),
    path(
        'paste-pages/',
        doc_views.paste_pages,
        name='paste_pages'
    ),
    path(
        'clipboard/',
        doc_views.clipboard,
        name='clipboard'
    ),
    path(
        'run-ocr/', doc_views.run_ocr_view, name="run_ocr"
    ),
    path(
        'api/documents',
        api_views.DocumentsView.as_view(),
        name='api_documents'
    ),
    path(
        'api/document/upload/<str:filename>',
        api_views.DocumentUploadView.as_view(),
        name='api_document_upload'
    ),
    path(
        'api/document/<int:pk>/',
        api_views.DocumentView.as_view(),
        name='api_document'
    ),
    path(
        'api/document/<int:doc_id>/pages',
        api_views.PagesView.as_view(),
        name='api_pages'
    ),
    path(
        'api/document/<int:doc_id>/pages/cut',
        api_views.PagesCutView.as_view(),
        name='api_pages_cut'
    ),
    path(
        'api/document/<int:doc_id>/pages/paste',
        api_views.PagesPasteView.as_view(),
        name='api_pages_paste'
    ),
    path(
        'user/<int:id>/change-password',
        users_views.user_change_password_view, name='user_change_password'
    ),
    path(
        'automate/',
        automate_views.automate_view,
        name="automate_view"
    ),
    path(
        'automate/<int:automate_id>/',
        automate_views.automate_change_view, name="automate_change_view"
    ),
]
