import gradio as gr
from gradio_canvaworkflow import canvaworkflow

# Exemple de données pour les agents/boîtes draggables
example_boxes = [
    {
        "id": "agent1",
        "label": "Recherche approfondie",
        "selected_model": "gpt-3.5-turbo",
    },
    {
        "id": "agent2",
        "label": "Envoi d'email",
        "selected_model": "gpt-4",
    },
    {
        "id": "agent3",
        "label": "Screening Client",
        "selected_model": "gpt-4",
    },
    {
        "id": "agent4",
        "label": "Traduction",
        "selected_model": "claude-3",
    },
]

# Exemple de workflow initial
example_workflow = {}
example_workflow = {
    "agents": [
        {
            "id": "agent1",
            "type": "agent",
            "statut": "active"
        },
        {
            "id": "agent3",
            "type": "agent",
            "statut": "inactive"
        },
        {
            "id": "email_1",
            "type": "email",
            "statut": "inactive"
        },
        
    ],
    "flow": [
        {
            "from": "agent1",
            "to": "agent3"
        },
        {
            "from": "agent3", 
            "to": "email_1"
        }
    ]
}

import os

# Obtenir le chemin du répertoire où se trouve ce script
current_dir = os.path.dirname(os.path.abspath(__file__))
css_path = os.path.join(current_dir, "custom_styles.css")

with open(css_path, "r") as f:
    custom_css = f.read()


def process_workflow(workflow_data):
    """Traite les données du workflow et retourne une version modifiée"""
    if not workflow_data:
        return {"nodes": [], "connections": []}

    import time

    processed_data = workflow_data.copy()
    if "agents" in processed_data:
        for agent in processed_data["agents"]:
            agent["processed_at"] = time.time()
    


with gr.Blocks(title="Canvas Workflow Demo", css=custom_css) as demo:
    gr.Markdown("# Canvas Workflow - Demo")
    gr.Markdown("Glissez-déposez les agents de la liste vers le canvas pour créer votre workflow.")
    gr.Markdown("**Petite croix** en haut à droite de chaque nœud pour le supprimer du workflow.")

    with gr.Row():
        with gr.Column(scale=2):
            workflow_component = canvaworkflow(
                value=example_workflow,
                boxes=example_boxes,
                label_list="Agents Disponibles",
                label_workflow="Workflow",
                show_label=None,
                elem_id="canvas-workflow",
                elem_classes=["canvas-workflow"],
            )

    # Connecter les composants
    workflow_component.change(
        fn=lambda x: x,
        inputs=[workflow_component],
        queue=False,
        show_progress="hidden",  # Passer directement les données
    )

    

if __name__ == "__main__":
    demo.launch()
