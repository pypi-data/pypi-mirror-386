from netbox.views import generic
from utilities.views import register_model_view

from cesnet_service_path_plugin.filtersets import ServicePathFilterSet
from cesnet_service_path_plugin.forms import (
    ServicePathBulkEditForm,
    ServicePathFilterForm,
    ServicePathForm,
)
from cesnet_service_path_plugin.models import ServicePath
from cesnet_service_path_plugin.tables import ServicePathTable


@register_model_view(ServicePath)
class ServicePathView(generic.ObjectView):
    queryset = ServicePath.objects.all()


@register_model_view(ServicePath, "list", path="", detail=False)
class ServicePathListView(generic.ObjectListView):
    queryset = ServicePath.objects.all()
    table = ServicePathTable
    filterset = ServicePathFilterSet
    filterset_form = ServicePathFilterForm


@register_model_view(ServicePath, "add", detail=False)
@register_model_view(ServicePath, "edit")
class ServicePathEditView(generic.ObjectEditView):
    queryset = ServicePath.objects.all()
    form = ServicePathForm


@register_model_view(ServicePath, "delete")
class ServicePathDeleteView(generic.ObjectDeleteView):
    queryset = ServicePath.objects.all()


@register_model_view(ServicePath, "bulk_edit", path="edit", detail=False)
class ServicePathBulkEditView(generic.BulkEditView):
    queryset = ServicePath.objects.all()
    filterset = ServicePathFilterSet
    table = ServicePathTable
    form = ServicePathBulkEditForm


@register_model_view(ServicePath, "bulk_delete", path="delete", detail=False)
class ServicePathBulkDeleteView(generic.BulkDeleteView):
    queryset = ServicePath.objects.all()
    filterset = ServicePathFilterSet
    table = ServicePathTable


@register_model_view(ServicePath, "bulk_import", path="import", detail=False)
class ServicePathBulkImportView(generic.BulkImportView):
    queryset = ServicePath.objects.all()
    model_form = ServicePathForm
    table = ServicePathTable
