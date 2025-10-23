# -*- coding: utf-8 -*-
import os, shutil
from fastcodedog.context.context import ctx_instance
from fastcodedog.prepare.pdm_to_model.after.additional_relationships import add_relationships
from fastcodedog.prepare.pdm_to_model.after.computed_properties import add_computed_properties
from fastcodedog.prepare.pdm_to_model.after.additional_methods import add_additional_methods
from fastcodedog.prepare.pdm_to_model.after.copy_methods import add_copy_methods
from fastcodedog.prepare.pdm_to_model.after.disable_relationships import disable_relationships
from fastcodedog.prepare.pdm_to_model.after.specified_class_names import add_specified_class_names
from fastcodedog.prepare.pdm_to_model.after.specified_relationship_orderby import specified_relationship_orderby
from fastcodedog.prepare.pdm_to_model.before.additional_foreign_keys import fill_additional_foreign_keys
from fastcodedog.prepare.pdm_to_model.before.fill_tenant_id import fill_tenant_id
from fastcodedog.prepare.pdm_to_model.before.specified_column_types import rename_specified_column_types
from fastcodedog.prepare.pdm_to_model.before.specified_relationship_names import add_specified_relationship_names
from fastcodedog.prepare.pdm_to_model.pdm import Pdm


def prepare_model(pre_process_scripts):
    # 先清空目录
    shutil.rmtree(ctx_instance.source_directory.model, ignore_errors=True)
    # 装载pdm文件
    pdm = Pdm(ctx_instance.source_directory.pdm_file)
    # 对pdm模型做一些批量的修改操作
    add_specified_class_names(pdm, pre_process_scripts['specified_class_names'])
    fill_additional_foreign_keys(pdm, pre_process_scripts['additional_foreign_keys'])
    add_specified_relationship_names(pdm, pre_process_scripts['specified_relationship_names'])
    rename_specified_column_types(pdm, pre_process_scripts['specified_column_types'])
    # 添加租户信息
    if ctx_instance.tenant.enabled:
        fill_tenant_id(pdm, ctx_instance.tenant.local_column_code, ctx_instance.tenant.foreign_table_code, ctx_instance.tenant.foreign_column_code)

    pdm.to_model()
    # 对导出后的model做些批量操作
    add_relationships(ctx_instance.source_directory.model, pre_process_scripts['additional_relationships'])
    disable_relationships(ctx_instance.source_directory.model, pre_process_scripts['disable_relationships'])
    # rename_specified_class_names(ctx_instance.source_directory.model, pre_process_scripts['specified_class_names'])
    add_computed_properties(ctx_instance.source_directory.model, pre_process_scripts['computed_properties'])
    specified_relationship_orderby(ctx_instance.source_directory.model, pre_process_scripts['specified_relationship_by'])
    add_additional_methods(ctx_instance.source_directory.model, pre_process_scripts['additional_methods'])
    add_copy_methods(ctx_instance.source_directory.model, pre_process_scripts['copy_methods'])
