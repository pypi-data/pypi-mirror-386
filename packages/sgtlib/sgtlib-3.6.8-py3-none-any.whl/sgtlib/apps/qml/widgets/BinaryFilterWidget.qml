import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: imgBinControls
    Layout.leftMargin: 10
    Layout.preferredHeight: 120
    Layout.preferredWidth: parent.width
    Layout.alignment: Qt.AlignTop
    spacing: 10
    visible: imageController.display_image()
    enabled: imageController.enable_img_controls()

    property int idRole: Qt.UserRole + 1
    property int valueRole: Qt.UserRole + 4
    property int btnWidthSize: 100
    property int spbWidthSize: 170
    property int sldWidthSize: 140
    property int lblWidthSize: 50

    ButtonGroup {
        id: btnGrpBinary
        property bool currentCheckedButton: rdoGlobal
        property bool clickedChange: false
        exclusive: true
        onCheckedButtonChanged: {
            if (clickedChange) {
                clickedChange = false
                return
            }

            if (currentCheckedButton !== checkedButton) {
                currentCheckedButton = checkedButton;
                var val = checkedButton === rdoGlobal ? 0 : checkedButton === rdoAdaptive ? 1 : 2;
                var index = imgBinFilterModel.index(0, 0);
                imgBinFilterModel.setData(index, val, valueRole);
                imageController.apply_changes("");
            }
        }
        onClicked: {
            clickedChange = true;
            currentCheckedButton = checkedButton;
            var val = checkedButton === rdoGlobal ? 0 : checkedButton === rdoAdaptive ? 1 : 2;
            var index = imgBinFilterModel.index(0, 0);
            imgBinFilterModel.setData(index, val, valueRole);
            imageController.apply_changes("binary");
        }
    }


    Text {
        text: "Binary Filters"
        font.pixelSize: 12
        font.bold: true
        Layout.alignment: Qt.AlignHCenter
    }

    RowLayout {

        RadioButton {
            id: rdoAdaptive
            text: "Adaptive"
            Layout.preferredWidth: btnWidthSize
            ButtonGroup.group: btnGrpBinary
            onClicked: btnGrpBinary.checkedButton = this
        }

        SpinBox {
            // ONLY ODD NUMBERS
            id: spbAdaptive
            Layout.minimumWidth: spbWidthSize
            //Layout.fillWidth: true
            from: 1
            to: 999
            stepSize: 2
            value: 11 // "adaptive_local_threshold_value"
            editable: true  // Allow user input
            enabled: rdoAdaptive.checked
            onValueChanged: {
                if (value % 2 === 0) {
                    value = value - 1;  // Convert even input to the nearest odd
                }

                var index = imgBinFilterModel.index(2, 0);
                imgBinFilterModel.setData(index, value, valueRole);
                imageController.apply_changes("");
            }
            validator: IntValidator {
                bottom: spbAdaptive.from; top: spbAdaptive.to
            }
        }
    }

    RowLayout {

        RadioButton {
            id: rdoGlobal
            text: "Global"
            Layout.preferredWidth: btnWidthSize
            ButtonGroup.group: btnGrpBinary
            onClicked: btnGrpBinary.checkedButton = this
        }

        Slider {
            id: sldGlobal
            Layout.minimumWidth: sldWidthSize
            Layout.fillWidth: true
            from: 1
            to: 255
            stepSize: 1
            value: 127  //"global_threshold_value"
            enabled: rdoGlobal.checked
            onValueChanged: {
                var index = imgBinFilterModel.index(1, 0);
                imgBinFilterModel.setData(index, value, valueRole);
                imageController.apply_changes("");
            }
        }

        Label {
            id: lblGlobal
            Layout.preferredWidth: lblWidthSize
            text: Number(sldGlobal.value).toFixed(0) // Display one decimal place
            enabled: rdoGlobal.checked
        }

    }

    RadioButton {
        id: rdoOtsu
        text: "OTSU"
        Layout.preferredWidth: btnWidthSize
        ButtonGroup.group: btnGrpBinary
        onClicked: btnGrpBinary.checkedButton = this
    }

    CheckBox {
        id: cbxDarkFg
        text: "Apply Dark Foreground"
        property bool clickedChange: false
        property bool isChecked: false
        checked: false
        onCheckedChanged: {
            if (clickedChange) {
                clickedChange = false
                return
            }

            if (isChecked !== checked) {
                isChecked = checked;
                var val = checked === true ? 1 : 0;
                var index = imgBinFilterModel.index(4, 0);
                imgBinFilterModel.setData(index, val, valueRole);
                imageController.apply_changes("");
            }
        }
        onClicked: {
            clickedChange = true;
            isChecked = checked;
            var val = checked === true ? 1 : 0;
            var index = imgBinFilterModel.index(4, 0);
            imgBinFilterModel.setData(index, val, valueRole);
            imageController.apply_changes("binary");
        }
    }

    function initializeSelections() {
        for (let row = 0; row < imgBinFilterModel.rowCount(); row++) {
            var index = imgBinFilterModel.index(row, 0);
            let item_id = imgBinFilterModel.data(index, idRole);  // IdRole
            let item_val = imgBinFilterModel.data(index, valueRole); // ValueRole

            if (item_id === "threshold_type") {
                btnGrpBinary.checkedButton = item_val === 2 ? rdoOtsu : item_val === 1 ? rdoAdaptive : rdoGlobal;
            } else if (item_id === "global_threshold_value") {
                sldGlobal.value = item_val;
            } else if (item_id === "adaptive_local_threshold_value") {
                spbAdaptive.value = item_val;
            } else if (item_id === "apply_dark_foreground") {
                cbxDarkFg.checked = item_val === 1;
            }
        }
    }

    Connections {
        target: mainController

        function onImageChangedSignal() {
            // Force refresh
            imgBinControls.visible = imageController.display_image();
            imgBinControls.enabled = imageController.enable_img_controls();
            initializeSelections();
        }

    }
}
