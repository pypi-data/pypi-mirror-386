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
from q2gui.q2model import Q2CursorModel
from q2gui.q2dialogs import q2Mess, q2AskYN

from q2rad.q2utils import Q2Form
from q2gui import q2app
import gettext


_ = gettext.gettext


class Q2Packages(Q2Form):
    def __init__(self, title=""):
        super().__init__("Packages")
        self.no_view_action = True

    def on_init(self):
        self.db = q2app.q2_app.db_logic
        self.add_control("package_name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("package_pipname", _("Pip name"), datatype="char", datalen=100)
        self.add_control("package_version", _("Version"), datatype="char", datalen=10)
        self.add_control("comment", _("Comment"), datatype="text")

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="packages")
        model = Q2CursorModel(cursor)
        model.set_order("package_name").refresh()
        self.set_model(model)
        self.add_action("/crud")
        # self.add_action("Imp", self.imp)
        self.add_action("Install", self.install, eof_disabled=True)
        self.add_action("Uninstall", self.uninstall, eof_disabled=True)
        self.add_action("Versions", self.info, eof_disabled=True)

    # def imp(self):
    #     __import__(self.r.package_name)
    #     current_version = self.q2_app.code_runner(
    #         f"import {self.r.package_name};return {self.r.package_name}.__version__"
    #     )()

    def uninstall(self):
        if q2AskYN(f"You are about tu uninstall package: {self.r.package_name}") == 2:
            self.q2_app.pip_uninstall(
                self.r.package_name if self.r.package_pipname == "" else self.r.package_pipname
            )

    def install(self):
        version = (
            self.r.package_version
            if self.r.package_version
            else self.q2_app.get_package_versions(self.r.package_name, self.r.package_pipname)[0]
        )
        if version:
            try:
                self.q2_app.pip_install(
                    self.r.package_name if self.r.package_pipname == "" else self.r.package_pipname, version
                )
            except Exception:
                q2Mess(_(f"pip install <b>{self.r.package_name}</b> error!"))
            finally:
                self.q2_app.code_runner(f"import {self.r.package_name}")()
        else:
            q2Mess(f"Package <b>{self.r.package_name}</b> not found!")

    def info(self):
        latest_version, current_version = self.q2_app.get_package_versions(
            self.r.package_name, self.r.package_pipname
        )
        # if not current_version:
        #     current_version = "Was not imported; "
        #     _cv = self.q2_app.code_runner(
        #         f"import {self.r.package_name};return {self.r.package_name}.__version__"
        #     )()
        #     current_version += f"Installed version: {_cv}"
        q2Mess(
            f"Package name: <b>{self.r.package_name}</b><br><br>"
            f"Installed version:<b>{current_version}</b><br><br>"
            f"Latest PYPI version:<b>{latest_version}</b>"
        )
