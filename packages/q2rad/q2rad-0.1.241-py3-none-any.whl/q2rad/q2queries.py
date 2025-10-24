#    Copyright © 2021 Andrei Puchko
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel, Q2Model
from q2gui.q2widget import Q2Widget
from q2gui.q2app import Q2Actions
from q2rad.q2utils import q2cursor, Q2_save_and_run, num
from q2gui.q2utils import set_dict_default
import json
import gettext
import re
from q2rad.q2utils import Q2Form
from q2gui import q2app

_ = gettext.gettext
re_find_param = re.compile(r"(?::\b\w+\b|\{.+\})")


class Q2Queries(Q2Form, Q2_save_and_run):
    def __init__(self, title=""):
        super().__init__("Queries")
        self.no_view_action = True

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="queries")
        model = Q2CursorModel(cursor)
        model.set_order("name").refresh()
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("JSON", self.edit_json, eof_disabled=1)

    def create_form(self):
        # self.query_editor_form = Q2QueryEdit()

        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("/")
        self.add_control("anchor", "**", control="label")
        # self.add_control("query_edit", "", widget=self.query_editor_form, nogrid=1, migrate=0)

        self.add_control(
            "content",
            "",
            datatype="longtext",
            control="codejson",
            nogrid=1,
            noform=1,
            # readonly=1,
        )
        self.add_control("comment", _("Comment"), datatype="longtext", noform=1)
        self.add_control("q2_time", "Time", datatype="int", noform=1, alignment=7)
        self._add_save_and_run(save_only=True)
        self._add_save_and_run_visible(save_only=True)

    def before_form_build(self):
        if self._save_and_run_control is None:
            self._save_and_run_control = self.controls.get("save_and_run_actions_visible")
            self.controls.delete("save_and_run_actions_visible")
        self.system_controls.insert(2, self._save_and_run_control)

    def before_form_show(self):
        self.maximized = True

    def after_form_show(self):
        self.anchor: Q2Widget = self.w.anchor
        if self.anchor is not None:
            self.anchor.set_visible(False)

            self.query_edit_container = Q2QueryEditContainer()
            w = self.query_edit_container.get_widget()
            self.widgets()["report_report"] = w
            self.query_edit_container.form_stack = [w]
            self.anchor.add_widget_below(w)
            self.query_edit_container.widget().restore_grid_columns()
            self.query_editor_form = self.query_edit_container.query_editor_form

        if self.crud_mode == "NEW":
            self.query_editor_form.set_content("")
        else:
            self.query_editor_form.set_content(self.r.content)
        self.query_editor_form.query_list.set_grid_index(0)

    def after_form_show0(self):
        self.anchor: Q2Widget = self.w.anchor

        if self.anchor is not None:
            self.anchor.set_visible(False)

            self.query_editor_form = Q2QueryEdit()
            w = self.query_editor_form.get_widget()
            self.widgets()["query_editor_form"] = w
            self.query_editor_form.form_stack = [w]
            self.anchor.add_widget_below(w)
            w.show()
            self.query_editor_form.widget().restore_grid_columns()
            w.restore_grid_columns()

        if self.crud_mode == "NEW":
            self.query_editor_form.set_content("{}")
        else:
            self.query_editor_form.set_content(self.r.content)

        self.query_editor_form.query_list.set_grid_index(0)
        self.query_editor_form.query_list.w.form__grid.set_focus()

    def before_crud_save(self):
        self.s.content = self.query_editor_form.get_content()

    def edit_json(self):
        form = Q2Form("Edit report JSON")
        json_editor_actions = Q2Actions()

        def save_json():
            json_file_name = form.q2_app.get_save_file_dialoq(filter="JSON(*.json)")[0]
            if json_file_name:
                json_file_name = form.validate_impexp_file_name(json_file_name, "json")
                open(json_file_name, "w", encoding="utf8").write(form.s.json)

        json_editor_actions.add_action("Save as", save_json, hotkey="")
        form.add_control("/v")
        form.add_control(
            "json",
            control="code_json",
            data=self.r.content,
            actions=json_editor_actions,
        )
        form.ok_button = 1
        form.cancel_button = 1
        form.run()
        if form.ok_pressed:
            self.model.update({"name": self.r.name, "content": form.s.json})
            self.set_grid_index(self.current_row)


class Q2QueryEditContainer(Q2Form):
    def __init__(self):
        super().__init__("Q E")

    def on_init(self):
        self.query_editor_form = Q2QueryEdit()
        self.add_control("/v")
        self.add_control("ql", "", widget=self.query_editor_form, nogrid=1, migrate=0)
        self.add_control("/")

    # def set_content(self, content):
    #     self.query_editor_form.set_content(content)

    # def get_content(self, str_mode=True):
    #     return self.query_editor_form.get_content(str_mode)


class Q2QueryEdit(Q2Form):
    def __init__(self):
        super().__init__("Query Edit")
        self.no_view_action = True
        self.lock_code_widget = False

    def on_init(self):
        self.query_list = Q2QueryList(self)
        self.param_list = Q2ParamList()
        self.actions = Q2Actions()
        self._db = None
        self.actions.add_action("Run F4", self.query_list.sql_runner, hotkey="F4")
        self.actions.add_action("Dataset|Show as JSON", self.query_list.show_dataset_json)
        self.actions.add_action("Dataset|Save as JSON", self.query_list.save_dataset_json)

        self.actions.show_main_button = 0
        self.actions.show_actions = 0
        self.add_control("/hs", tag="qeh")
        self.add_control("hot_key_action", actions=self.actions, control="toolbar")
        if self.add_control("/vs", tag="qev"):
            self.add_control("ql", "", widget=self.query_list, nogrid=1, migrate=0)
            if self.add_control("/h"):
                self.add_control("/s")
                self.add_control(
                    "run_query_button",
                    "Run (F4)",
                    valid=self.query_list.sql_runner,
                    control="button",
                )
                self.add_control("/s")
            self.add_control("/")
            self.add_control("pl", "", widget=self.param_list, nogrid=1, migrate=0)
            self.add_control("/")
        self.add_control("code", control="codesql", nogrid=1, valid=self.sql_changed)
        self.add_control("/")

    def set_content(self, content):
        if isinstance(content, str):
            if content:
                content_json = json.loads(content)
            else:
                content_json = {}
        else:
            content_json = content
        self.query_list.set_content(content_json.get("queries", {"new_query": "select * from "}))
        self.param_list.set_content(content_json.get("params", []))
        self.param_list.put_params(self.get_all_sql())

    def get_content(self, str_mode=True):
        queries = self.query_list.get_content()
        params = self.param_list.get_content()

        content = {"queries": queries, "params": params}
        if str_mode:
            return json.dumps(content, indent=2)
        else:
            return content

    def after_form_show(self):
        self.w.run_query_button.fix_default_height()
        self.w.hot_key_action.set_visible(0)
        self.query_list.grid_index_changed()
        self.query_list.w.form__grid.set_focus()

    def sql_changed(self):
        if self.lock_code_widget is True:
            return
        self.query_list.sql_to_model(self.s.code)
        self.param_list.put_params(self.get_all_sql())

    def get_all_sql(self):
        return " ".join([x.get("sql", "") for x in self.query_list.model.records])


class Q2QueryList(Q2Form):
    def __init__(self, query_editor_form):
        super().__init__("QueryList")
        self.i_am_child = True
        self.query_editor_form = query_editor_form
        self.no_view_action = True
        self.add_control("name", "Name", datatype="char", datalen="50")
        self.add_control("sql", "Sql", datatype="longtext", nogrid=1, noform=1)
        self.add_control("/")
        self.set_model(Q2Model())
        self.add_action("/crud")
        self.add_action("-")
        self.add_action("Dataset|Show as JSON", self.show_dataset_json)
        self.add_action("Dataset|Save as JSON", self.save_dataset_json)
        
        self.model.readonly = False
        self.last_current_row = -1

    def after_form_show(self):
        if self.crud_mode != "EDIT":
            start_value = self.r.name
            while True:
                _pkvalue_list = re.split(r"([^\d]+)", start_value)
                _base = "".join(_pkvalue_list[:-1])
                _suffix = num(_pkvalue_list[-1]) + 1
                start_value = f"{_base}{_suffix}"
                if start_value not in [row["name"] for row in self.model.records]:
                    break
            self.s.name = start_value

    def set_content(self, content):
        self.model.reset()
        for x in content:
            self.model.insert({"name": x, "sql": content[x]})
        self.refresh()

    def sql_runner(self):
        sql = self.r.sql
        params = re_find_param.findall(sql)
        for x in params:
            value = self.query_editor_form.param_list.get_param(x)
            if x[1] == "_":
                sql = sql.replace(x, f"{value}")
            else:
                sql = sql.replace(x, f"'{value}'")
        q2cursor(sql, q2_db=self.query_editor_form._db).browse()

    def prepare_dataset_json(self):
        dataset_json = {"params": {}}
        for query in self.model.get_records():
            sql = query["sql"]
            params = re_find_param.findall(sql)
            for x in params:
                value = self.query_editor_form.param_list.get_param(x)
                dataset_json["params"][x] = value
                if x[1] == "_":
                    sql = sql.replace(x, f"{value}")
                else:
                    sql = sql.replace(x, f"'{value}'")
            cu = q2cursor(sql, q2_db=self.query_editor_form._db)
            rez = []
            for x in cu.records():
                rez.append(x)
            dataset_json[query["name"]] = rez
        return dataset_json

    def show_dataset_json(self):
        dataset_json = self.prepare_dataset_json()

        if dataset_json:
            json_form = Q2Form()
            json_form.add_control("json", "", control="codejson", data=json.dumps(dataset_json, indent=2))
            json_form.ok_button = True
            json_form.show_form("JSON datasets")

    def save_dataset_json(self):
        dataset_json = self.prepare_dataset_json()

        if dataset_json:
            json_file_name = self.q2_app.get_save_file_dialoq(filter="JSON(*.json)")[0]
            if json_file_name:
                json_file_name = self.validate_impexp_file_name(json_file_name, "json")
                open(json_file_name, "w", encoding="utf8").write(json.dumps(dataset_json, indent=2))

    def sql_to_model(self, sql):
        self.model.update({"sql": sql}, self.current_row, refresh=False)

    def grid_index_changed(self):
        if self.current_row < 0:
            return
        sql = self.model.get_record(self.current_row).get("sql", "")
        self.query_editor_form.lock_code_widget = True
        self.query_editor_form.s.code = sql
        self.query_editor_form.lock_code_widget = False

    def before_crud_save(self):
        if self.crud_mode == "NEW":
            self.s.sql = "select *\nfrom "

    def get_content(self):
        content = {x["name"]: x["sql"] for x in self.model.records}
        return content


class Q2ParamList(Q2Form):
    def __init__(self):
        super().__init__("ParamList")
        self.i_am_child = True
        self.no_view_action = True
        self.add_control("name", "Name", datatype="char", datalen="50", disabled="*")
        self.add_control("value", "Value", datatype="text", control="codesql")
        self.add_control("hidden", "Hidden", datatype="char", datalen=1, nogrid=1, noform=1)
        self.add_control("/")
        self.set_model(Q2Model())
        self.add_action_edit()
        self.model.readonly = False

    def set_content(self, content):
        content = [{"name": x, "value": content[x]} for x in content]
        self.model.reset()
        names = []
        for x in content:
            set_dict_default(x, "name", "name")
            if x["name"] in names:
                continue
            else:
                names.append(x["name"])
            set_dict_default(x, "value", "")
            set_dict_default(x, "hidden", "")
            self.model.insert(x)

    def get_content(self):
        params = {}
        for param in self.model.records:
            param = dict(param)
            if param["hidden"] != "":
                continue
            del param["hidden"]
            params[param["name"]] = param["value"]
        return params

    def get_param(self, param):
        for x in self.model.records:
            if x["name"] == (param[1:] if param.startswith(":") else param[1:-1]):
                return x["value"]
        return ""

    def put_params(self, sql):
        params = set(re_find_param.findall(sql))
        params = {x[1:] if x.startswith(":") else x[1:-1] for x in params}
        names = {}
        for x in range(len(self.model.records)):
            names[self.model.records[x]["name"]] = x
        for x in params:
            if x in names:
                self.model.records[names[x]]["hidden"] = ""
            else:
                self.model.insert({"name": x, "value": "", "hidden": ""})
        for x in names:
            if x not in params:
                self.model.records[names[x]]["hidden"] = "*"

        self.model.set_order("name")
        self.model.set_where("hidden==''")
