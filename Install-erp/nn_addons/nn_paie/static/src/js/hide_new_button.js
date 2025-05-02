/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Fonction qui observe le DOM et masque le bouton New dès qu'il apparaît
 */
function hideNewButtonInEmployeeDialog() {
    // Fonction pour masquer le bouton
    function hideButton() {
        const dialogs = document.querySelectorAll('.modal-dialog');

        dialogs.forEach(dialog => {
            // Vérifier si c'est la boîte de dialogue des employés
            const title = dialog.querySelector('.modal-title');
            if (title && (title.textContent.includes('Employees') || title.textContent.includes('Employés'))) {

                // Trouver tous les boutons dans le footer
                const buttons = dialog.querySelectorAll('.modal-footer button');

                // Parcourir les boutons et cacher celui qui s'appelle "New" ou "Nouveau"
                buttons.forEach(button => {
                    if ((button.textContent.trim() === 'New' || button.textContent.trim() === 'Nouveau') &&
                        !button.classList.contains('o_select_button')) {
                        console.log("Masquage du bouton New/Nouveau");
                        button.style.display = 'none';
                    }
                });
            }
        });
    }

    // Observer les changements dans le DOM
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.addedNodes.length) {
                // Attendre un moment pour que le DOM soit complètement chargé
                setTimeout(hideButton, 100);
            }
        }
    });

    // Commencer à observer tout le body pour détecter quand les dialogues sont ajoutés
    observer.observe(document.body, { childList: true, subtree: true });

    // Exécuter également au démarrage
    document.addEventListener('DOMContentLoaded', hideButton);

    // Ajouter également un gestionnaire d'événement pour les clics qui pourraient ouvrir des dialogues
    document.body.addEventListener('click', () => {
        setTimeout(hideButton, 200);
    });

    console.log("Observateur pour masquer le bouton New dans les dialogues d'employés est actif");
}

// Enregistrer la fonction pour qu'elle soit exécutée au démarrage
registry.category("web_start").add("nn_paie.hide_new_button_direct", hideNewButtonInEmployeeDialog);