// src/setupTests.ts
import "@testing-library/jest-dom/vitest";

// jsdom does not implement <dialog>: open and close it by hand.
HTMLDialogElement.prototype.showModal = function () {
	this.open = true;
};
HTMLDialogElement.prototype.close = function () {
	this.open = false;
};
