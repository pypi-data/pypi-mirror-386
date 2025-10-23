from PyQt6 import QtWidgets, QtCore, QtGui, sip
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import sys
import os
import csv
import json


class GuiSpark:
    def __init__(self, title="PyQt GUI Manager", width=600, height=400):
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle(title)
        self.window.resize(width, height)

        self.central = QtWidgets.QWidget()
        self.window.setCentralWidget(self.central)
        
        # Layout principal para melhor organização
        self.main_layout = QtWidgets.QVBoxLayout(self.central)
        
        self.widgets = {}
        self.current_focus = None

    def _build_stylesheet(self, wtype, bg=None, fg=None, hover_bg=None, pressed_bg=None, border_radius=None):
        """Constrói a folha de estilo de forma mais robusta"""
        styles = []
        
        base_props = []
        if bg:
            base_props.append(f"background-color: {bg}")
        if fg:
            base_props.append(f"color: {fg}")
        if border_radius:
            base_props.append(f"border-radius: {border_radius}px")
        
        if base_props:
            if wtype == 'button':
                styles.append(f"QPushButton {{ {'; '.join(base_props)} }}")
            elif wtype == 'label':
                styles.append(f"QLabel {{ {'; '.join(base_props)} }}")
            elif wtype == 'frame':
                styles.append(f"QFrame {{ {'; '.join(base_props)} }}")
            elif wtype == 'entry':
                styles.append(f"QLineEdit {{ {'; '.join(base_props)} }}")
            elif wtype == 'text':
                styles.append(f"QTextEdit {{ {'; '.join(base_props)} }}")
            elif wtype == 'checkbox':
                styles.append(f"QCheckBox {{ {'; '.join(base_props)} }}")
            elif wtype == 'web':
                styles.append(f"QWebEngineView {{ {'; '.join(base_props)} }}")
            elif wtype == 'slider':
                styles.append(f"QSlider {{ {'; '.join(base_props)} }}")
            elif wtype == 'progress':
                styles.append(f"QProgressBar {{ {'; '.join(base_props)} }}")
            elif wtype == 'combobox':
                styles.append(f"QComboBox {{ {'; '.join(base_props)} }}")
            else:
                styles.append(f"{'; '.join(base_props)}")
        
        if wtype == 'button':
            if hover_bg:
                styles.append(f"QPushButton:hover {{ background-color: {hover_bg} }}")
            if pressed_bg:
                styles.append(f"QPushButton:pressed {{ background-color: {pressed_bg} }}")
        
        return "".join(styles)

    def add_widget(self, wtype, x=0, y=0, width=100, height=30, text="", bg=None, fg=None,
                   hover_bg=None, pressed_bg=None, border_radius=None, command=None, parent=None,
                   placeholder="", url=None, min_value=0, max_value=100, value=0, 
                   items=None, orientation='horizontal'):
        """
        Adiciona um widget
        
        Args:
            wtype: button, label, frame, entry, text, checkbox, web, slider, progress, combobox
            min_value/max_value: Para sliders e progress bars
            value: Valor inicial
            items: Lista de itens para combobox
            orientation: 'horizontal' ou 'vertical' para slider
        """
        parent = parent or self.central

        if wtype == 'button':
            widget = QtWidgets.QPushButton(text, parent)
        elif wtype == 'label':
            widget = QtWidgets.QLabel(text, parent)
        elif wtype == 'frame':
            widget = QtWidgets.QFrame(parent)
            widget.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        elif wtype == 'entry':
            widget = QtWidgets.QLineEdit(parent)
            if text:
                widget.setText(text)
            if placeholder:
                widget.setPlaceholderText(placeholder)
        elif wtype == 'text':
            widget = QtWidgets.QTextEdit(parent)
            if text:
                widget.setText(text)
            if placeholder:
                widget.setPlaceholderText(placeholder)
        elif wtype == 'checkbox':
            widget = QtWidgets.QCheckBox(text, parent)
            widget.setChecked(bool(value))
        elif wtype == 'web':
            widget = QWebEngineView(parent)
            if url:
                if url.startswith(('http://', 'https://')):
                    widget.load(QUrl(url))
                else:
                    widget.setHtml(url)
            elif text:
                widget.setHtml(text)
        elif wtype == 'slider':  # NOVO: Slider
            widget = QtWidgets.QSlider(parent)
            if orientation == 'horizontal':
                widget.setOrientation(QtCore.Qt.Orientation.Horizontal)
            else:
                widget.setOrientation(QtCore.Qt.Orientation.Vertical)
            widget.setMinimum(min_value)
            widget.setMaximum(max_value)
            widget.setValue(value)
        elif wtype == 'progress':  # NOVO: Progress Bar
            widget = QtWidgets.QProgressBar(parent)
            widget.setMinimum(min_value)
            widget.setMaximum(max_value)
            widget.setValue(value)
        elif wtype == 'combobox':  # NOVO: Combobox
            widget = QtWidgets.QComboBox(parent)
            if items:
                widget.addItems(items)
            if text:
                widget.setCurrentText(text)
        else:
            raise ValueError(f"Tipo de widget desconhecido: {wtype}")

        stylesheet = self._build_stylesheet(wtype, bg, fg, hover_bg, pressed_bg, border_radius)
        if stylesheet:
            widget.setStyleSheet(stylesheet)

        widget.setGeometry(x, y, width, height)

        if command and wtype in ['button', 'checkbox', 'slider', 'combobox']:
            if wtype == 'button':
                widget.clicked.connect(command)
            elif wtype == 'checkbox':
                widget.stateChanged.connect(command)
            elif wtype == 'slider':
                widget.valueChanged.connect(command)
            elif wtype == 'combobox':
                widget.currentTextChanged.connect(command)

        wid = id(widget)
        self.widgets[wid] = {'widget': widget, 'type': wtype}
        widget.show()
        return wid

    def remove_widget(self, wid):
        """Remove um widget pelo ID"""
        if wid in self.widgets:
            widget = self.widgets[wid]['widget']
            if widget.parent() and hasattr(widget.parent(), 'layout') and widget.parent().layout():
                widget.parent().layout().removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
            del self.widgets[wid]

    def add_layout_widget(self, wtype, text="", bg=None, fg=None, command=None, placeholder="", 
                         url=None, min_value=0, max_value=100, value=0, items=None, orientation='horizontal'):
        """Adiciona widget no layout (melhor para responsividade)"""
        if wtype == 'button':
            widget = QtWidgets.QPushButton(text)
        elif wtype == 'label':
            widget = QtWidgets.QLabel(text)
        elif wtype == 'entry':
            widget = QtWidgets.QLineEdit()
            if placeholder:
                widget.setPlaceholderText(placeholder)
        elif wtype == 'checkbox':
            widget = QtWidgets.QCheckBox(text)
            widget.setChecked(bool(value))
        elif wtype == 'web':
            widget = QWebEngineView()
            if url:
                if url.startswith(('http://', 'https://')):
                    widget.load(QUrl(url))
                else:
                    widget.setHtml(url)
            elif text:
                widget.setHtml(text)
        elif wtype == 'slider':  # NOVO: Slider no layout
            widget = QtWidgets.QSlider()
            if orientation == 'horizontal':
                widget.setOrientation(QtCore.Qt.Orientation.Horizontal)
            else:
                widget.setOrientation(QtCore.Qt.Orientation.Vertical)
            widget.setMinimum(min_value)
            widget.setMaximum(max_value)
            widget.setValue(value)
        elif wtype == 'progress':  # NOVO: Progress Bar no layout
            widget = QtWidgets.QProgressBar()
            widget.setMinimum(min_value)
            widget.setMaximum(max_value)
            widget.setValue(value)
        elif wtype == 'combobox':  # NOVO: Combobox no layout
            widget = QtWidgets.QComboBox()
            if items:
                widget.addItems(items)
            if text:
                widget.setCurrentText(text)
        else:
            raise ValueError(f"Tipo não suportado para layout: {wtype}")
        
        stylesheet = self._build_stylesheet(wtype, bg, fg)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
        
        if command and wtype in ['button', 'checkbox', 'slider', 'combobox']:
            if wtype == 'button':
                widget.clicked.connect(command)
            elif wtype == 'checkbox':
                widget.stateChanged.connect(command)
            elif wtype == 'slider':
                widget.valueChanged.connect(command)
            elif wtype == 'combobox':
                widget.currentTextChanged.connect(command)
        
        self.main_layout.addWidget(widget)
        wid = id(widget)
        self.widgets[wid] = {'widget': widget, 'type': wtype}
        return wid

    def get_widget_text(self, wid):
        """Obtém texto/valor de um widget"""
        if wid in self.widgets:
            widget = self.widgets[wid]['widget']
            wtype = self.widgets[wid]['type']
            
            if wtype in ['entry']:
                return widget.text()
            elif wtype in ['text']:
                return widget.toPlainText()
            elif wtype in ['label', 'button']:
                return widget.text()
            elif wtype == 'checkbox':
                return widget.isChecked()
            elif wtype == 'web':
                return widget.url().toString()
            elif wtype == 'slider':  # NOVO: Valor do slider
                return widget.value()
            elif wtype == 'progress':  # NOVO: Valor do progress
                return widget.value()
            elif wtype == 'combobox':  # NOVO: Texto selecionado no combobox
                return widget.currentText()
        return None

    def set_widget_text(self, wid, text):
        """Define texto/valor de um widget"""
        if wid in self.widgets:
            widget = self.widgets[wid]['widget']
            wtype = self.widgets[wid]['type']
            if wtype in ['entry']:
                widget.setText(str(text))
            elif wtype in ['text']:
                widget.setPlainText(str(text))
            elif wtype in ['label', 'button']:
                widget.setText(str(text))
            elif wtype == 'checkbox':
                widget.setChecked(bool(text))
            elif wtype == 'web':
                if str(text).startswith(('http://', 'https://')):
                    widget.load(QUrl(str(text)))
                else:
                    widget.setHtml(str(text))
            elif wtype == 'slider':  # NOVO: Setar valor do slider
                try:
                    widget.setValue(int(text))
                except (ValueError, TypeError):
                    pass
            elif wtype == 'progress':  # NOVO: Setar valor do progress
                try:
                    widget.setValue(int(text))
                except (ValueError, TypeError):
                    pass
            elif wtype == 'combobox':  # NOVO: Setar texto no combobox
                widget.setCurrentText(str(text))

    def set_widget_visibility(self, wid, visible):
        """Mostra/oculta widget"""
        if wid in self.widgets:
            widget = self.widgets[wid]['widget']
            widget.setVisible(visible)

    def set_widget_enabled(self, wid, enabled):
        """Habilita/desabilita widget"""
        if wid in self.widgets:
            widget = self.widgets[wid]['widget']
            widget.setEnabled(enabled)

    def clear_container(self, parent_wid=None):
        """Limpa todos widgets de um container"""
        parent = self.central if not parent_wid else self.widgets[parent_wid]['widget']
        for child in parent.findChildren(QtWidgets.QWidget):
            if child != parent:
                child_id = id(child)
                if child_id in self.widgets:
                    self.remove_widget(child_id)

    def show_message(self, title, message, message_type="info"):
        """Exibe caixa de mensagem"""
        if message_type == "info":
            QtWidgets.QMessageBox.information(self.window, title, message)
        elif message_type == "warning":
            QtWidgets.QMessageBox.warning(self.window, title, message)
        elif message_type == "error":
            QtWidgets.QMessageBox.critical(self.window, title, message)

    # ========== SISTEMA DE TEMAS ==========

    def set_theme(self, theme_name="light"):
        """Aplica um tema pré-definido à interface"""
        themes = {
            "dark": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "widget_bg": "#3c3f41",
                "widget_fg": "#ffffff",
                "accent": "#bb86fc"
            },
            "light": {
                "bg": "#f5f5f5",
                "fg": "#333333",
                "widget_bg": "#ffffff",
                "widget_fg": "#333333",
                "accent": "#2196F3"
            },
            "blue": {
                "bg": "#e3f2fd",
                "fg": "#1565c0",
                "widget_bg": "#bbdefb",
                "widget_fg": "#0d47a1",
                "accent": "#1976d2"
            },
            "green": {
                "bg": "#e8f5e8",
                "fg": "#2e7d32",
                "widget_bg": "#c8e6c9",
                "widget_fg": "#1b5e20",
                "accent": "#4caf50"
            }
        }
        
        # CORREÇÃO: Usar 'light' como padrão se o tema não existir
        theme = themes.get(theme_name, themes["light"])
        
        # Aplicar tema ao central widget
        self.central.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['bg']};
                color: {theme['fg']};
            }}
            QPushButton {{
                background-color: {theme['widget_bg']};
                color: {theme['widget_fg']};
                border: 1px solid {theme['accent']};
                padding: 5px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {theme['widget_bg']};
                color: {theme['widget_fg']};
                border: 1px solid {theme['accent']};
                border-radius: 3px;
                padding: 2px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {theme['accent']};
                height: 8px;
                background: {theme['widget_bg']};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']};
                border: 1px solid {theme['accent']};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
            QProgressBar {{
                border: 1px solid {theme['accent']};
                border-radius: 4px;
                text-align: center;
                background: {theme['widget_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 3px;
            }}
        """)

    # ========== VALIDAÇÃO DE ENTRADA ==========

    def set_input_validation(self, wid, validation_type="text", max_length=None, regex=None):
        """
        Configura validação para campos de entrada
        
        Args:
            wid: ID do widget
            validation_type: 'text', 'number', 'email', 'custom'
            max_length: Comprimento máximo
            regex: Expressão regular personalizada
        """
        if wid not in self.widgets:
            return
        
        widget = self.widgets[wid]['widget']
        wtype = self.widgets[wid]['type']
        
        if wtype not in ['entry', 'text']:
            return
        
        if max_length:
            widget.setMaxLength(max_length)
        
        if validation_type == "number":
            from PyQt6.QtGui import QDoubleValidator
            validator = QDoubleValidator()
            widget.setValidator(validator)
        elif validation_type == "integer":
            from PyQt6.QtGui import QIntValidator
            validator = QIntValidator()
            widget.setValidator(validator)
        elif validation_type == "email":
            import re
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            from PyQt6.QtGui import QRegularExpressionValidator
            from PyQt6.QtCore import QRegularExpression
            regex = QRegularExpression(email_regex)
            validator = QRegularExpressionValidator(regex)
            widget.setValidator(validator)
        elif validation_type == "custom" and regex:
            from PyQt6.QtGui import QRegularExpressionValidator
            from PyQt6.QtCore import QRegularExpression
            regex_obj = QRegularExpression(regex)
            validator = QRegularExpressionValidator(regex_obj)
            widget.setValidator(validator)

    # ========== EVENTOS AVANÇADOS ==========

    def add_mouse_event(self, wid, event_type="click", command=None):
        """
        Adiciona eventos de mouse a widgets
        
        Args:
            wid: ID do widget
            event_type: 'click', 'double_click', 'enter', 'leave'
            command: Função a ser executada
        """
        if wid not in self.widgets or not command:
            return
        
        widget = self.widgets[wid]['widget']
        
        if event_type == "click":
            # CORREÇÃO: Preservar o evento original
            original_event = widget.mousePressEvent
            def new_event(event):
                command()
                if original_event:
                    original_event(event)
            widget.mousePressEvent = new_event
            
        elif event_type == "double_click":
            original_event = widget.mouseDoubleClickEvent
            def new_event(event):
                command()
                if original_event:
                    original_event(event)
            widget.mouseDoubleClickEvent = new_event
            
        elif event_type == "enter":
            original_event = widget.enterEvent
            def new_event(event):
                command()
                if original_event:
                    original_event(event)
            widget.enterEvent = new_event
            
        elif event_type == "leave":
            original_event = widget.leaveEvent
            def new_event(event):
                command()
                if original_event:
                    original_event(event)
            widget.leaveEvent = new_event

    def add_key_event(self, wid, key=None, command=None):
        """
        Adiciona eventos de teclado
        
        Args:
            wid: ID do widget
            key: Tecla específica (ex: QtCore.Qt.Key_Return)
            command: Função a ser executada
        """
        if wid not in self.widgets or not command:
            return
        
        widget = self.widgets[wid]['widget']
        
        if key:
            original_event = widget.keyPressEvent
            def new_event(event):
                if event.key() == key:
                    command()
                if original_event:
                    original_event(event)
            widget.keyPressEvent = new_event
        else:
            original_event = widget.keyPressEvent
            def new_event(event):
                command()
                if original_event:
                    original_event(event)
            widget.keyPressEvent = new_event

    # ========== FUNÇÕES PARA MANIPULAÇÃO DE ARQUIVOS ==========

    def save_to_file(self, data, filename=None, file_type=None, mode="w", separator=","):
        """
        Salva dados em arquivo com extensão escolhida pelo usuário
        """
        if filename is None:
            filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
                self.window, 
                "Salvar Arquivo", 
                "", 
                "Todos os arquivos (*);;Text files (*.txt);;CSV files (*.csv);;JSON files (*.json)"
            )
            if not filename:
                return False
            
            if selected_filter:
                if "txt" in selected_filter:
                    file_type = "txt"
                elif "csv" in selected_filter:
                    file_type = "csv"
                elif "json" in selected_filter:
                    file_type = "json"
        
        if file_type is None and filename:
            ext = os.path.splitext(filename)[1].lower().replace('.', '')
            if ext in ['txt', 'csv', 'json']:
                file_type = ext
            else:
                file_type = 'txt'
        
        try:
            with open(filename, mode, encoding='utf-8') as file:
                if file_type == 'txt':
                    if isinstance(data, list):
                        if any('\n' in str(item) for item in data) or any(separator in str(item) for item in data):
                            file.write('\n'.join(str(item) for item in data))
                        else:
                            file.write(separator.join(str(item) for item in data))
                    else:
                        file.write(str(data))
                
                elif file_type == 'csv':
                    if isinstance(data, list):
                        if all(isinstance(item, (list, tuple)) for item in data):
                            writer = csv.writer(file)
                            writer.writerows(data)
                        else:
                            writer = csv.writer(file)
                            writer.writerow(data)
                    else:
                        file.write(str(data))
                
                elif file_type == 'json':
                    if isinstance(data, (dict, list)):
                        json.dump(data, file, indent=4, ensure_ascii=False)
                    else:
                        file.write(str(data))
                
                else:
                    file.write(str(data))
            
            self.show_message("Sucesso", f"Arquivo salvo: {filename}", "info")
            return True
            
        except Exception as e:
            self.show_message("Erro", f"Erro ao salvar arquivo: {str(e)}", "error")
            return False

    def read_from_file(self, filename=None, file_type=None):
        """
        Lê dados de um arquivo e retorna o conteúdo
        """
        if filename is None:
            filename, selected_filter = QtWidgets.QFileDialog.getOpenFileName(
                self.window,
                "Abrir Arquivo",
                "",
                "Todos os arquivos (*);;Text files (*.txt);;CSV files (*.csv);;JSON files (*.json)"
            )
            if not filename:
                return None
            
            if selected_filter:
                if "txt" in selected_filter:
                    file_type = "txt"
                elif "csv" in selected_filter:
                    file_type = "csv"
                elif "json" in selected_filter:
                    file_type = "json"
        
        if file_type is None and filename:
            ext = os.path.splitext(filename)[1].lower().replace('.', '')
            if ext in ['txt', 'csv', 'json']:
                file_type = ext
            else:
                file_type = 'txt'
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                if file_type == 'txt':
                    content = file.read()
                    if ',' in content and '\n' not in content:
                        return [item.strip() for item in content.split(',')]
                    elif '\n' in content:
                        return [line.strip() for line in content.split('\n') if line.strip()]
                    else:
                        return content
                
                elif file_type == 'csv':
                    reader = csv.reader(file)
                    rows = list(reader)
                    if len(rows) == 1:
                        return rows[0]
                    else:
                        return rows
                
                elif file_type == 'json':
                    return json.load(file)
                
                else:
                    return file.read()
                    
        except Exception as e:
            self.show_message("Erro", f"Erro ao ler arquivo: {str(e)}", "error")
            return None

    def append_to_file(self, data, filename=None, file_type=None, separator=","):
        """
        Adiciona dados a um arquivo existente
        """
        return self.save_to_file(data, filename, file_type, mode="a", separator=separator)

    def run(self):
        self.window.show()
        return self.app.exec()