const MAX_FILE_SIZE = 100 * 1024 * 1024;

function showToast(message) {
    const toast = document.querySelector("[data-toast]");
    if (!toast) {
        return;
    }

    toast.textContent = message;
    toast.classList.add("is-visible");
    window.setTimeout(() => toast.classList.remove("is-visible"), 2200);
}

function updateFileLabel(input) {
    const dropZone = input.closest(".drop-zone");
    const label = dropZone?.querySelector("[data-file-label]");
    const file = input.files?.[0];

    if (!label || !file) {
        return;
    }

    if (file.size > MAX_FILE_SIZE) {
        label.textContent = "This file is larger than 100 MB.";
        label.style.color = "var(--danger)";
        input.value = "";
        return;
    }

    const size = file.size < 1024 * 1024
        ? (file.size / 1024).toFixed(2) + " KB"
        : (file.size / (1024 * 1024)).toFixed(2) + " MB";
    label.textContent = file.name + " - " + size;
    label.style.color = "var(--accent)";
}

function bindDropZone(input) {
    const dropZone = input.closest(".drop-zone");
    if (!dropZone) {
        return;
    }

    input.addEventListener("change", () => updateFileLabel(input));

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("drag-over");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        const files = event.dataTransfer?.files;
        if (!files || files.length === 0) {
            return;
        }

        input.files = files;
        updateFileLabel(input);
    });
}

function bindForms() {
    document.querySelectorAll("[data-form]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const fileInput = form.querySelector("[data-file-input]");
            const file = fileInput?.files?.[0];
            const hashInput = form.querySelector("#expected_hash");

            if (!file) {
                event.preventDefault();
                showToast("Please choose a file before submitting.");
                return;
            }

            if (file.size > MAX_FILE_SIZE) {
                event.preventDefault();
                showToast("File is too large. Maximum size is 100 MB.");
                return;
            }

            if (hashInput && !hashInput.value.trim()) {
                event.preventDefault();
                showToast("Paste a hash value before verifying.");
                return;
            }

            form.classList.add("is-submitting");
        });
    });
}

function bindCopyButtons() {
    document.querySelectorAll("[data-copy]").forEach((button) => {
        button.addEventListener("click", async () => {
            const text = button.getAttribute("data-copy") || "";

            try {
                await navigator.clipboard.writeText(text);
                showToast("Hash copied to clipboard.");
            } catch (_error) {
                showToast("Copy failed. Select the hash and copy manually.");
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-file-input]").forEach(bindDropZone);
    bindForms();
    bindCopyButtons();
});
