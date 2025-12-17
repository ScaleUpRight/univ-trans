/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
const { Component, useRef, useState, onMounted, onWillUnmount } = owl;

export class CameraDialog extends Component {

    setup() {
        super.setup();

        this.video = useRef("video");
        this.image = useRef("image");

        this.stream = null;

        this.state = useState({
            img: false,
            facingMode: "environment",
            zoom: 1,
        });

        onMounted(() => {
            console.log("📷 Camera Mounted");
            this.openCamera();
        });

        onWillUnmount(() => {
            this.stopCamera();
        });
    }


    async openCamera() {
        try {
            this.stopCamera();

            const constraints = {
                video: {
                    facingMode: this.state.facingMode,
                },
                audio: false,
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.el.srcObject = this.stream;
        } catch (error) {
            console.error("❌ Camera error:", error);
        }
    }


    stopCamera() {
        try {
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
        } catch (e) {}
    }

    async _switchCamera() {
        this.state.facingMode =
            this.state.facingMode === "user" ? "environment" : "user";

        this.state.zoom = 1;
        await this.openCamera();
        this._applyZoom();
    }

    _zoomIn() {
        this.state.zoom = Math.min(this.state.zoom + 0.2, 4);
        this._applyZoom();
    }

    _zoomOut() {
        this.state.zoom = Math.max(this.state.zoom - 0.2, 1);
        this._applyZoom();
    }

    _applyZoom() {
        const video = this.video.el;
        if (!video) return;

        video.style.transform = `scale(${this.state.zoom})`;
        video.style.transformOrigin = "center center";
    }


    _confirm() {
        const video = this.video.el;
        const image = this.image.el;

        const zoom = this.state.zoom || 1;
        const vw = video.videoWidth;
        const vh = video.videoHeight;

        const canvas = document.createElement("canvas");
        canvas.width = vw;
        canvas.height = vh;

        const ctx = canvas.getContext("2d");

        const sw = vw / zoom;
        const sh = vh / zoom;
        const sx = (vw - sw) / 2;
        const sy = (vh - sh) / 2;

        ctx.drawImage(
            video,
            sx, sy, sw, sh,   // source (cropped)
            0, 0, vw, vh      // destination
        );

        this.state.img = canvas.toDataURL("image/jpeg", 0.9);
        this.img_binary = this.state.img.split(",")[1];

        video.classList.add("d-none");
        image.classList.remove("d-none");
        image.src = this.state.img;
    }

    _save() {
        this.props.parent.props.record.update({
            [this.props.parent.props.name]: this.img_binary,
        });

        this.props.parent.state.isValid = true;
        this.env.dialogData.close();
        this.stopCamera();
    }

    _reset() {
        this.img_binary = false;
        this.state.img = false;

        this.video.el.classList.remove("d-none");
        this.image.el.classList.add("d-none");

        this.state.zoom = 1;
        this._applyZoom();
    }

    _cancel() {
        this.env.dialogData.close();
        this.stopCamera();
    }
}

CameraDialog.template = "bd_camera_image_capture.camera_dialog";
CameraDialog.components = { Dialog };
