"use strict";

/*
 * RootLearn — Landing Page
 * This file currently handles small frontend interactions.
 * Authentication, diagnostics and database operations
 * will be implemented in later stages.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Keep the copyright year current.
    const yearElement = document.getElementById("current-year");

    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    // Give navigation links a smooth, accessible scroll.
    const sectionLinks = document.querySelectorAll(
        'a[href^="#"]'
    );

    sectionLinks.forEach((link) => {
        link.addEventListener("click", (event) => {
            const targetId = link.getAttribute("href");

            if (!targetId || targetId === "#") {
                return;
            }

            const target = document.querySelector(targetId);

            if (!target) {
                return;
            }

            event.preventDefault();

            target.scrollIntoView({
                behavior: window.matchMedia(
                    "(prefers-reduced-motion: reduce)"
                ).matches ? "auto" : "smooth",
                block: "start"
            });
        });
    });

    console.info("RootLearn landing page initialized.");
});