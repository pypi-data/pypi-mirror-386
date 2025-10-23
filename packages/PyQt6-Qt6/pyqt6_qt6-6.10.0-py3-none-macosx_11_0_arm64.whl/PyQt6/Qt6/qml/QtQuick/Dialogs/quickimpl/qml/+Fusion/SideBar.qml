// Copyright (C) 2024 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.Controls.Fusion
import QtQuick.Controls.impl
import QtQuick.Dialogs.quickimpl as DialogsQuickImpl

DialogsQuickImpl.SideBar {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    contentWidth: (contentItem as ListView)?.contentWidth

    background: Rectangle {
        color: control.palette.window
        x: 1
        y: 1
        width: parent.width - 2
        height: parent.height - 2
        radius: 2
    }

    contentItem: ListView {
        id: listView
        currentIndex: control.currentIndex
        model: control.contentModel
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {}

        Rectangle {
            anchors.fill: parent
            color: control.palette.light
            border.color: control.palette.mid
            z: -1
        }
    }

    buttonDelegate: Button {
        id: buttonDelegateRoot
        flat: true
        highlighted: control.currentIndex === index
        width: listView.width

        contentItem: IconLabel {
            spacing: 5
            leftPadding: 10
            topPadding: 3
            bottomPadding: 3
            icon: buttonDelegateRoot.icon
            text: buttonDelegateRoot.folderName
            font: buttonDelegateRoot.font
            alignment: Qt.AlignLeft
        }

        required property int index
        required property string folderName
    }

    separatorDelegate: Item {
        implicitWidth: control.width
        implicitHeight: 9
        Rectangle {
            id: separatorDelegate
            color: Qt.lighter(Fusion.darkShade, 1.06)
            anchors.centerIn: parent
            radius: 1
            height: 1
            width: parent.width - 10
        }
    }

    addFavoriteDelegate: Button {
        id: addFavoriteDelegateRoot
        text: qsTr("Add Favorite")
        flat: true
        width: control.width
        contentItem: IconLabel {
            spacing: 5
            leftPadding: 10
            topPadding: 3
            bottomPadding: 3
            icon: addFavoriteDelegateRoot.icon
            text: addFavoriteDelegateRoot.labelText
            font: addFavoriteDelegateRoot.font
            opacity: addFavoriteDelegateRoot.dragHovering ? 0.2 : 1.0
            alignment: Qt.AlignLeft
        }

        required property string labelText
        required property bool dragHovering
    }
}
