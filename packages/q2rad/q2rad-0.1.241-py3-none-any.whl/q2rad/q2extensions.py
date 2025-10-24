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


import os
from datetime import datetime
from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2dialogs import q2Mess, q2AskYN, q2working

from q2rad.q2utils import Q2Form
from q2gui import q2app
from q2rad.q2appmanager import AppManager
from q2terminal.q2terminal import Q2Terminal
import gettext
import json
from q2rad.q2raddb import read_url
from q2gui.q2model import Q2Model


_ = gettext.gettext


class Q2Extensions(Q2Form):
    def __init__(self, title=""):
        super().__init__("Extensions")
        self.no_view_action = True

    def on_init(self):
        self.db = q2app.q2_app.db_data
        self.add_control("prefix", _("Name"), datatype="char", datalen=50, pk="*")
        self.add_control("seq", _("Sequence number"), datatype="int")
        self.add_control("version", _("Version"), datatype="char", datalen=16, readonly=True)
        self.add_control("q2market_path", _("q2market folder"), datatype="char", datalen=255)
        self.add_control("q2market_url", _("q2market url"), datatype="char", datalen=255)
        self.add_control("checkupdates", _("Check for updates"), control="check", datatype="char", datalen=1)
        self.add_control("comment", _("Comment"), datatype="text")

        cursor: Q2Cursor = self.q2_app.db_data.table(table_name="extensions")
        model = Q2CursorModel(cursor)
        model.set_order("seq").refresh()
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("Export|as JSON file", self.export_json, eof_disabled=True)
        # if os.path.isdir(self.q2_app.q2market_path):
        self.add_action("Export|to q2Market", self.export_q2market, eof_disabled=True)
        self.add_action("Import|from JSON file", self.import_json, eof_disabled=True)
        self.add_action("Import|from q2Market", self.import_q2market, eof_disabled=True)

    def before_form_show(self):
        if self.crud_mode == "NEW":
            if q2AskYN("Would you like to download one from q2market?") == 2:
                q2market = Q2MarketExt().run()
                if q2market.heap._return:
                    self.s.prefix = q2market.heap._return
                    self.s.checkupdates = "*"

    def info(self):
        pass

    def export_json(self, file=""):
        prefix = self.r.prefix
        filetype = "JSON(*.json)"
        if not file:
            desktop = os.path.expanduser("~/Desktop")
            file = f"{desktop}/{prefix}.json"
            file, filetype = q2app.q2_app.get_save_file_dialoq(
                f"Export Extension ({prefix})", filter=filetype, path=file
            )
        if not file:
            return
        file = self.validate_impexp_file_name(file, filetype)
        if file:

            def get_ext_json(prefix=prefix):
                return AppManager._get_app_json(prefix)

            ext_json = q2working(get_ext_json, "Prepare data...")
            if ext_json:
                json.dump(ext_json, open(file, "w"), indent=1)

    def import_json(self, file=""):
        prefix = self.r.prefix
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq(
                f"Import Extension ({prefix})", filter=filetype
            )

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        if data:
            AppManager.import_json_app(data, prefix=prefix)
            self.q2_app.open_selected_app()

    def export_q2market(self):
        prefix = self.r.prefix
        q2market_path = self.r.q2market_path if self.r.q2market_path else self.q2_app.q2market_path
        q2market_url = self.r.q2market_url if self.r.q2market_url else self.q2_app.q2market_url
        if not os.path.isdir(q2market_path):
            q2Mess("No q2market path!")
            return
        if not q2market_url:
            q2Mess("No App URL!")
            return
        if (
            q2AskYN(
                f"<p>You are about to export Extension (<b>{prefix}</b>) "
                f"<p>into folder {os.path.abspath(q2market_path)}"
                f"<p>and  upload into  {os.path.abspath(q2market_url)}"
                "<p>Are you sure?"
            )
            != 2
        ):
            return

        q2market_file = f"{q2market_path}/q2market.json"
        if os.path.isfile(q2market_file):
            q2market = json.load(open(q2market_file))
        else:
            q2market = {}

        version = datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")
        ext_url = f"{q2market_url}/{prefix}"
        q2market[ext_url] = {
            "ext_title": prefix,
            "ext_version": version,
            "ext_description": self.r.comment,
        }
        json.dump(q2market, open(q2market_file, "w"), indent=2)
        open(f"{q2market_path}/{prefix}.version", "w").write(version)
        self.db.update("extensions", {"prefix": prefix, "version": version})

        self.export_json(f"{q2market_path}/{prefix}.json")

        trm = Q2Terminal(callback=print)

        def worker():
            trm.run(f"cd {q2market_path}")
            trm.run("git add -A")
            trm.run(f"""git commit -a -m"{version}"  """)

        q2working(worker, "Commiting")
        q2Mess(trm.run("""git push"""))
        trm.close()

    def import_q2market(self):
        q2market_url = self.r.q2market_url if self.r.q2market_url else self.q2_app.q2market_url
        if q2market_url:
            if q2app.q2_app.check_ext_update(self.r.prefix, force_update=True):
                q2app.q2_app.open_selected_app()
        else:
            q2Mess("No App URL!")


class Q2MarketExt(Q2Form):
    def __init__(self, title=""):
        super().__init__("q2Market")
        self.no_view_action = True
        self.heap._return = None

    def on_init(self):
        self.add_control("ext_title", _("Name"), datatype="char", datalen=100)
        self.add_control("ext_version", _("Version"), datatype="char", datalen=100)
        self.add_control("ext_description", _("Description"), control="text", datatype="char", datalen=100)
        self.add_control("ext_url", _("Path"), datatype="char", datalen=100)

        q2market_catalogue_url = f"{self.q2_app.q2market_url}/q2market.json"
        data = json.loads(read_url(q2market_catalogue_url).decode("utf-8"))
        rez = []
        for x in data:
            if "ext_title" in data[x]:
                rec = data[x]
                rec["ext_url"] = x
                rez.append(rec)
        model = Q2Model()
        model.set_records(rez)
        self.set_model(model)
        self.add_action_view()
        self.add_action("Select", self.select_row, tag="select", eof_disabled=1)

    def select_row(self):
        self.heap._return = self.r.ext_title
        self.close()
