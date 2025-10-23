import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: microscopyProps
    Layout.preferredHeight: 80
    Layout.preferredWidth: parent.width - 75

    property int txtWidthSize: 70
    property int lblWidthSize: 80
    property int valueRole: Qt.UserRole + 4

    ColumnLayout {
        id: microscopyPropsLayout

        Repeater {
            model: microscopyPropsModel
            delegate: RowLayout {
                visible: model.visible === 1

                Label {
                    id: label
                    wrapMode: Text.Wrap
                    color: "#2266ff"
                    font.pixelSize: 10
                    Layout.preferredWidth: lblWidthSize
                    Layout.leftMargin: 10
                    text: model.text
                }

                TextField {
                    id: txtField
                    objectName: model.id
                    color: "#2266ff"
                    font.pixelSize: 10
                    Layout.preferredWidth: txtWidthSize
                    text: model.value
                    onActiveFocusChanged: {
                        if (focus) {
                            btnOK.visible = true;
                        }
                    }
                }

                Button {
                    id: btnOK
                    text: ""
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 26
                    Layout.rightMargin: 10
                    visible: false
                    onClicked: {
                        btnOK.visible = false;

                        let index = microscopyPropsModel.index(model.index, 0);
                        microscopyPropsModel.setData(index, txtField.text, valueRole);
                        //console.log(txtField.text);
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5
                        color: "#22bc55"

                        Label {
                            text: "OK"
                            color: "#ffffff"
                            //font.bold: true
                            //font.pixelSize: 10
                            anchors.centerIn: parent
                        }
                    }
                }
            }
        }
    }
}
