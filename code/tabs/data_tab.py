import os
import sys
import pandas as pd
import sqlite3
import csv
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog


class DataTab(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'DataTab.ui'), self)



        self.mat_button.clicked.connect(self.select_mat_folder)


        self.mat_default_button.clicked.connect(self.set_default)

        self.uv_background_button.clicked.connect(self.select_file)

        self.uv_background_default_button.clicked.connect(self.set_default)

        self.nir_background_button.clicked.connect(self.select_file)

        self.nir_background_default_button.clicked.connect(self.set_default)

        self.nir_silicon_button.clicked.connect(self.select_file)

        self.nir_silicon_default_button.clicked.connect(self.set_default)
        self.uv_silicon_button.clicked.connect(self.select_file)

        self.uv_silicon_default_button.clicked.connect(self.set_default)
        self.ref_silicon_button.clicked.connect(self.select_file)

        self.ref_silicon_default_button.clicked.connect(self.set_default)

        self.uv_sample_button.clicked.connect(self.select_file)

        self.uv_sample_default_button.clicked.connect(self.set_default)
        self.nir_sample_button.clicked.connect(self.select_file)

        self.nir_sample_default_button.clicked.connect(self.set_default)

        self.create_data_base()
        self.apply_default()
        self.check_if_can_send()

    def check_if_can_send(self):
        if os.path.exists(self.mat_folder.text()) and os.path.exists(self.uv_background_file.text()) and os.path.exists(
                self.nir_background_file.text()) and os.path.exists(self.uv_silicon_file.text()) and os.path.exists(
            self.nir_silicon_file.text()) and os.path.exists(self.ref_silicon_file.text()) and os.path.exists(
            self.uv_sample_file.text()) and os.path.exists(self.nir_sample_file.text()):
            return True
        else:
            print("one or more file paths are not valid")
            return False


    def send_data(self):
        data = {}
        data["mat_folder"] = self.mat_folder.text()
        data["background_uv_file"] = self.uv_background_file.text()
        data["background_nir_file"] = self.nir_background_file.text()
        data["silicon_uv_file"] = self.uv_silicon_file.text()
        data["silicon_nir_file"] = self.nir_silicon_file.text()
        data["silicon_reference_file"] = self.ref_silicon_file.text()
        data["sample_uv_file"] = self.uv_sample_file.text()
        data["sample_nir_file"] = self.nir_sample_file.text()
        data["scaling"] = self.scaling_input.value()
        return data

    def create_data_base(self):
        connection = sqlite3.connect("data_base.db")
        cursor = connection.cursor()
        table = cursor.execute(
            """SELECT name FROM sqlite_master WHERE type='table' AND name='data_tab_default'""").fetchall()

        if table == []:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS data_tab_default (button_file_name TEXT,button_default_name TEXT,output_name TEXT, file_path TEXT)""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("mat_button","mat_default_button","mat_folder","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("uv_background_button","uv_background_default_button","uv_background_file","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("nir_background_button","nir_background_default_button","nir_background_file","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("uv_silicon_button","uv_silicon_default_button","uv_silicon_file","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("nir_silicon_button","nir_silicon_default_button","nir_silicon_file","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("ref_silicon_button","ref_silicon_default_button","ref_silicon_file","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("uv_sample_button","uv_sample_default_button","uv_sample_file","")""")
            cursor.execute(
                """INSERT INTO data_tab_default VALUES ("nir_sample_button","nir_sample_default_button","nir_sample_file","")""")

        else:
            pass

        cursor.close()
        connection.commit()
        connection.close()

    def apply_default(self):
        connection = sqlite3.connect("data_base.db")
        cursor = connection.cursor()
        rows = cursor.execute("""SELECT * FROM data_tab_default""").fetchall()
        for row in rows:
            output = self.findChild(QtWidgets.QLineEdit, row[2])
            output.setText(row[3])
        cursor.close()
        connection.close()

    def select_mat_folder(self):
        folder = QFileDialog.getExistingDirectory()
        if folder == "":
            return
        self.mat_folder.setText(folder)
        self.check_if_can_send()


    def select_file(self):
        file, _ = QFileDialog.getOpenFileName()
        if file == "":
            return

        connection = sqlite3.connect("data_base.db")
        cursor = connection.cursor()
        button_name = self.sender().objectName()
        output_name = cursor.execute("SELECT output_name FROM data_tab_default WHERE button_file_name = ?",
                                     (button_name,), ).fetchall()

        self.findChild(QtWidgets.QLineEdit, output_name[0][0]).setText(file)
        cursor.close()
        connection.commit()
        connection.close()
        self.check_if_can_send()


    def set_default(self):
        connection = sqlite3.connect("data_base.db")
        cursor = connection.cursor()
        button_name = self.sender().objectName()

        rows = cursor.execute("SELECT output_name FROM data_tab_default WHERE button_default_name = ?",
                              (button_name,), ).fetchall()
        output_name = rows[0][0]
        file_path = self.findChild(QtWidgets.QLineEdit, output_name).text()
        cursor.execute("UPDATE data_tab_default SET file_path = ? WHERE button_default_name = ?",
                       (file_path, button_name,))
        cursor.close()
        connection.commit()
        connection.close()
