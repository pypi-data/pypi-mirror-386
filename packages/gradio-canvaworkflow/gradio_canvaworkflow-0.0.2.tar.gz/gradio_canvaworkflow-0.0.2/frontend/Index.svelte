<svelte:options accessors={true} />

<script lang="ts">
	// Imports des types et composants Gradio
	import type { Gradio } from "@gradio/utils";
	import { BlockTitle, Block } from "@gradio/atoms";
	import { StatusTracker } from "@gradio/statustracker";
	import type { LoadingStatus } from "@gradio/statustracker";

	// Props exportées depuis Gradio
	export let gradio: Gradio<{
		change: never;
		submit: never;
		input: never;
		clear_status: LoadingStatus;
	}>;
	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let visible = true;
	// Structure de données principale : nœuds et connexions
	export let value: { nodes?: any[]; connections?: any[] } = {
		nodes: [],
		connections: [],
	};
	export let show_label: boolean;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;
	export let loading_status: LoadingStatus | undefined = undefined;
	export let value_is_output = false;

	// Configuration des agents et labels
	export let boxes: any[] = [];
	export let label_list = "Agents";
	export let label_workflow = "Workflow";

	// Variables d'état pour le workflow
	let nodes: any[] = [];
	let connections: any[] = [];
	// Gestion du pan (déplacement de la vue)
	let offset = { x: 0, y: 0 };
	let isPanning = false;
	// Gestion du drag & drop des nœuds
	let isDraggingNode = false;
	// Gestion des connexions entre nœuds
	let isConnecting = false;
	let connectionStart: number | null = null;
	let tempConnection: {
		from: { x: number; y: number };
		to: { x: number; y: number };
	} | null = null;
	// Variables pour le pan
	let panStart = { x: 0, y: 0 };
	// Variables pour le drag des nœuds
	let nodeDragIndex: number | null = null;
	let nodeDragOffset = { x: 0, y: 0 };
	let dragStartPosition = { x: 0, y: 0 };
	let hasDraggedNode = false;
	// Référence au conteneur du workflow
	let workflowRef: HTMLDivElement;
	// Gestion de la configuration email
	let showEmailConfig = false;
	let emailConfigNodeId: string | null = null;
	let emailRecipients = "";
	let currentEmailNode: any = null;
	let recipientFields: string[] = [""];

	// Réactivité : synchronisation avec les props
	// Init nodes et connections depuis value
	$: if (value?.nodes) nodes = value.nodes;
	$: if (value?.connections) connections = value.connections;

	// Nouveau format : convertir depuis agents/flow (uniquement pour l'initialisation)
	$: if (value?.agents && value?.flow && !nodes.length) {
		const convertedData = convertFromAgentsFlow(value);
		nodes = convertedData.nodes;
		connections = convertedData.connections;
	}

	// Fonction pour convertir le format agents/flow en nodes/connections
	function convertFromAgentsFlow(data: any) {
		if (!data.agents) return { nodes: [], connections: [] };

		// Créer un mapping ID -> index pour retrouver facilement les agents
		const agentMap = new Map();
		data.agents.forEach((agent: any, index: number) => {
			agentMap.set(agent.id, index);
		});

		// Placer les nœuds en grille
		const convertedNodes = data.agents.map((agent: any, index: number) => {
			const row = Math.floor(index / 3); // 3 colonnes max
			const col = index % 3;
			const x = 50 + col * 150; // Espacement horizontal
			const y = 50 + row * 100; // Espacement vertical

			return {
				id: `node_${agent.id}`,
				id_original: agent.id,
				label: agent.id, // Utiliser l'ID comme label pour le moment
				type: agent.type,
				statut: agent.statut || "inactive", // Statut par défaut
				x,
				y,
			};
		});

		// Créer les connexions
		const convertedConnections = (data.flow || [])
			.map((connection: any, index: number) => {
				const fromIndex = agentMap.get(connection.from);
				const toIndex = agentMap.get(connection.to);

				return {
					id: `conn_${fromIndex}_${toIndex}`,
					from: fromIndex,
					to: toIndex,
				};
			})
			.filter(
				(conn: any) => conn.from !== undefined && conn.to !== undefined,
			);

		return {
			nodes: convertedNodes,
			connections: convertedConnections,
		};
	}

	// Envoi à Gradio - gestion des changements d'état
	function handle_change() {
		const flowData = {
			agents: nodes.map((node) => ({
				id: node.id_original || node.id,
				label: node.label,
				type: node.type || "agent",
				statut: node.statut || "inactive",
				...(node.type === "email" &&
					node.recipients && {
						recipients: node.recipients,
					}),
			})),
			flow: connections.map((conn) => ({
				from: nodes[conn.from]?.id_original || nodes[conn.from]?.id,
				to: nodes[conn.to]?.id_original || nodes[conn.to]?.id,
			})),
		};
		value = flowData;
		gradio.dispatch("change");
		if (!value_is_output) gradio.dispatch("input");
	}

	// Déclencher la synchronisation à chaque modification
	$: nodes, connections, handle_change();

	// Gestion du pan (déplacement de la vue globale)
	function handleMouseDownPan(e: MouseEvent) {
		if (
			(e.target as HTMLElement).dataset.type === "node" ||
			(e.target as HTMLElement).dataset.type === "connector"
		)
			return;
		// Annuler la connexion en cours si on clique ailleurs
		if (isConnecting) {
			isConnecting = false;
			connectionStart = null;
			tempConnection = null;
			return;
		}
		isPanning = true;
		panStart = { x: e.clientX - offset.x, y: e.clientY - offset.y };
	}

	function handleMouseMovePan(e: MouseEvent) {
		// Pan de la vue si on est en mode pan
		if (isPanning && !isDraggingNode) {
			offset = { x: e.clientX - panStart.x, y: e.clientY - panStart.y };
		}

		// Affichage de la connexion temporaire en mode connexion
		if (isConnecting && connectionStart !== null && workflowRef) {
			const rect = workflowRef.getBoundingClientRect();
			const startNode = nodes[connectionStart];
			// Calculer le centre vertical de la boîte de départ
			const startNodeElement = document.getElementById(
				`${elem_id}-node-${connectionStart}`,
			);
			const nodeHeight = startNodeElement
				? startNodeElement.offsetHeight
				: 30; // fallback si élément non trouvé
			const fromX = startNode.x + (startNode.type === "email" ? 40 : 100);
			const fromY = startNode.y + nodeHeight / 2;
			const toX = e.clientX - rect.left - offset.x;
			const toY = e.clientY - rect.top - offset.y;
			tempConnection = {
				from: { x: fromX, y: fromY },
				to: { x: toX, y: toY },
			};
		}

		// Gestion du drag des nœuds
		if (isDraggingNode) handleNodeMouseMove(e);
	}

	function handleMouseUpPan() {
		isPanning = false;
		// Arrêter la connexion si relâchement souris
		if (isConnecting) {
			isConnecting = false;
			connectionStart = null;
			tempConnection = null;
		}
		// Réinitialiser le drag des nœuds
		isDraggingNode = false;
		nodeDragIndex = null;
		hasDraggedNode = false;
	}

	// Drag interne des nœuds
	function handleNodeMouseDown(e: MouseEvent, index: number) {
		// Éviter le conflit avec les connecteurs et les boutons
		if ((e.target as HTMLElement).dataset.type === "connector") return;
		if ((e.target as HTMLElement).classList.contains("delete-button"))
			return;
		if ((e.target as HTMLElement).classList.contains("config-email-button"))
			return;
		isDraggingNode = true;
		nodeDragIndex = index;
		hasDraggedNode = false;
		const rect = workflowRef.getBoundingClientRect();
		// Position de départ pour détecter le mouvement
		dragStartPosition = {
			x: e.clientX,
			y: e.clientY,
		};
		// Offset de la souris par rapport au nœud
		nodeDragOffset = {
			x: e.clientX - rect.left - nodes[index].x - offset.x,
			y: e.clientY - rect.top - nodes[index].y - offset.y,
		};
	}

	// Ouverture de la config email via bouton dédié
	function handleEmailConfigClick(e: MouseEvent, index: number) {
		e.stopPropagation();
		openEmailConfig(index);
	}

	// Suppression de nœud avec bouton croix
	function deleteNode(index: number) {
		// Si on n'a qu'un seul nœud, vider complètement le tableau
		if (nodes.length === 1) {
			nodes = [];
			connections = [];
			// Forcer handle_change manuellement
			handle_change();
			return;
		}

		// Supprimer le nœud
		nodes = nodes.filter((_, i) => i !== index);

		// Supprimer toutes les connexions liées à ce nœud
		connections = connections.filter(
			(conn) => conn.from !== index && conn.to !== index,
		);

		// Réindexer les connexions pour les nœuds restants
		connections = connections.map((conn) => ({
			...conn,
			from: conn.from > index ? conn.from - 1 : conn.from,
			to: conn.to > index ? conn.to - 1 : conn.to,
		}));

		// Forcer la mise à jour (déclencher la réactivité)
		nodes = [...nodes];
		connections = [...connections];
	}

	function handleNodeMouseMove(e: MouseEvent) {
		if (isDraggingNode && nodeDragIndex !== null && workflowRef) {
			// Détecter si on a bougé la souris suffisamment pour considérer que c'est un drag
			const dragDistance = Math.sqrt(
				Math.pow(e.clientX - dragStartPosition.x, 2) +
					Math.pow(e.clientY - dragStartPosition.y, 2),
			);

			if (dragDistance > 3) {
				// Seuil de 3 pixels
				hasDraggedNode = true;
			}

			// Calculer la nouvelle position du nœud
			const rect = workflowRef.getBoundingClientRect();
			const newX = e.clientX - rect.left - offset.x - nodeDragOffset.x;
			const newY = e.clientY - rect.top - offset.y - nodeDragOffset.y;
			nodes[nodeDragIndex] = {
				...nodes[nodeDragIndex],
				x: newX,
				y: newY,
			};
		}
	}

	// Drag depuis la liste d'agents
	function handleDragStart(e: DragEvent, box: any) {
		e.dataTransfer?.setData("text/plain", JSON.stringify(box));
		(e.target as HTMLElement).style.cursor = "grabbing";
	}
	function handleDragEnd(e: DragEvent) {
		(e.target as HTMLElement).style.cursor = "grab";
	}

	// Connexions entre nœuds
	// Commencer une connexion depuis un nœud
	function startConnection(e: MouseEvent, index: number) {
		e.stopPropagation();
		isConnecting = true;
		connectionStart = index;
	}

	// Terminer une connexion sur un nœud
	function endConnection(e: MouseEvent, index: number) {
		e.stopPropagation();
		if (
			isConnecting &&
			connectionStart !== null &&
			connectionStart !== index
		) {
			const newConnection = {
				id: `conn_${connectionStart}_${index}`,
				from: connectionStart,
				to: index,
			};
			connections = [...connections, newConnection];
			tempConnection = null;
			isConnecting = false;
			connectionStart = null;
		}
	}

	// Courbe SVG pour les connexions
	function createCurvedPath(
		fromX: number,
		fromY: number,
		toX: number,
		toY: number,
	) {
		const deltaX = toX - fromX;
		// Points de contrôle pour la courbe de Bézier
		const control1X = fromX + Math.abs(deltaX) * 0.5;
		const control1Y = fromY;
		const control2X = toX - Math.abs(deltaX) * 0.5;
		const control2Y = toY;
		return `M ${fromX} ${fromY} C ${control1X} ${control1Y}, ${control2X} ${control2Y}, ${toX} ${toY}`;
	}

	// Gestion de la configuration email
	function openEmailConfig(nodeIndex: number) {
		const node = nodes[nodeIndex];
		if (node.type === "email") {
			currentEmailNode = node;
			showEmailConfig = true;
			emailConfigNodeId = node.id;
			// Récupérer les destinataires existants
			if (node.recipients && node.recipients.length > 0) {
				recipientFields = [...node.recipients];
			} else {
				recipientFields = [""];
			}
		}
	}

	function closeEmailConfig() {
		showEmailConfig = false;
		emailConfigNodeId = null;
		currentEmailNode = null;
		recipientFields = [""];
	}

	function saveEmailConfig() {
		if (currentEmailNode) {
			// Filtrer les champs vides
			const recipients = recipientFields
				.map((email) => email.trim())
				.filter((email) => email.length > 0);

			// Trouver l'index du nœud et mettre à jour
			const nodeIndex = nodes.findIndex(
				(n) => n.id === currentEmailNode.id,
			);
			if (nodeIndex !== -1) {
				nodes[nodeIndex] = {
					...nodes[nodeIndex],
					recipients: recipients,
				};
			}
		}
		closeEmailConfig();
	}

	// Gestion des champs de destinataires multiples
	function addRecipientField() {
		recipientFields = [...recipientFields, ""];
	}

	function removeRecipientField(index: number) {
		if (recipientFields.length > 1) {
			recipientFields = recipientFields.filter((_, i) => i !== index);
		}
	}
</script>

<!-- Composant principal Gradio Block -->
<Block
	{visible}
	{elem_id}
	{elem_classes}
	{scale}
	{min_width}
	allow_overflow={false}
	padding={true}
>
	{#if loading_status}
		<!-- Indicateur de statut de chargement -->
		<StatusTracker
			{...loading_status}
			i18n={gradio.i18n}
			autoscroll={gradio.autoscroll}
			on:clear_status={() =>
				gradio.dispatch("clear_status", loading_status)}
		/>
	{/if}

	<!-- Conteneur principal du workflow canvas -->

	<div class="canvas-workflow-container" id="{elem_id}-container">
		<!-- Layout principal : liste agents + canvas -->
		<div class="workflow-main" id="{elem_id}-main">
			<!-- Panneau latéral : liste des agents -->
			<div class="agents-list" id="{elem_id}-agents-list">
				<div class="agents-header">
					<h3 id="{elem_id}-agents-title">{label_list}</h3>
				</div>
				<!-- Conteneur des agents draggables -->
				<div class="boxes-container" id="{elem_id}-boxes-container">
					{#each boxes as box, i}
						<div
							class="draggable-box"
							id="{elem_id}-box-{i}"
							draggable="true"
							role="button"
							tabindex="0"
							on:dragstart={(e) => handleDragStart(e, box)}
							on:dragend={handleDragEnd}
						>
							{box.label}
						</div>
					{/each}
				</div>
			</div>

			<!-- Zone principale de travail : workflow canvas -->
			<div class="workflow-canvas" id="{elem_id}-workflow-canvas">
				<div class="workflow-header">
					<h3 id="{elem_id}-workflow-title">{label_workflow}</h3>
					<!-- Bouton Email en haut à droite -->
					<div
						class="email-button"
						id="{elem_id}-email-button"
						draggable="true"
						role="button"
						tabindex="0"
						title="Glisser pour ajouter un bloc Email"
						on:dragstart={(e) =>
							handleDragStart(e, {
								label: "Email",
								type: "email",
							})}
						on:dragend={handleDragEnd}
						on:keydown={(e) => {
							if (e.key === "Enter" || e.key === " ") {
								e.preventDefault();
								// Optionally trigger drag behavior
							}
						}}
					>
						<img
							src="https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg"
							alt="Gmail"
							class="email-button-icon"
						/>
					</div>
				</div>

				<!-- Menu de configuration Email (popup) -->
				{#if showEmailConfig}
					<div class="email-config-panel" id="{elem_id}-email-config">
						<div class="email-config-header">
							<h4>Configuration Email</h4>
							<button
								class="close-config-button"
								on:click={closeEmailConfig}
								aria-label="Fermer la configuration"
								title="Fermer">×</button
							>
						</div>
						<div class="email-config-content">
							<label>Destinataires :</label>
							<!-- Liste des champs destinataires -->
							{#each recipientFields as recipient, index}
								<div class="recipient-field-container">
									<input
										type="email"
										bind:value={recipientFields[index]}
										placeholder="email@example.com"
										class="recipient-input"
									/>
									{#if recipientFields.length > 1}
										<button
											class="remove-recipient-button"
											on:click={() =>
												removeRecipientField(index)}
											aria-label="Supprimer ce destinataire"
											title="Supprimer">×</button
										>
									{/if}
								</div>
							{/each}
							<!-- Ajouter un nouveau destinataire -->
							<button
								class="add-recipient-button"
								on:click={addRecipientField}
								title="Ajouter un destinataire">+</button
							>
							<div class="email-config-buttons">
								<button
									class="btn-save"
									on:click={saveEmailConfig}
									>Sauvegarder</button
								>
							</div>
						</div>
					</div>
				{/if}
				<!-- Zone interactive de dessin du workflow -->
				<!-- svelte-ignore a11y-no-static-element-interactions -->
				<div
					class="canvas-area"
					id="{elem_id}-canvas-area"
					bind:this={workflowRef}
					role="application"
					aria-label="Workflow canvas"
					on:dragover={(e) => e.preventDefault()}
					on:drop={(e) => {
						e.preventDefault();
						// Récupération des données de l'agent/élément droppé
						const boxData = JSON.parse(
							e.dataTransfer?.getData("text/plain") || "{}",
						);
						const rect = workflowRef.getBoundingClientRect();
						const x = e.clientX - rect.left - offset.x;
						const y = e.clientY - rect.top - offset.y;
						// Création d'un nouveau nœud
						nodes = [
							...nodes,
							{
								...boxData,
								x,
								y,
								id: `node_${Date.now()}`,
								id_original: boxData.id, // Conserver l'ID original de l'agent
								statut: boxData.statut || "inactive", // Statut par défaut
							},
						];
					}}
					on:mousedown={handleMouseDownPan}
					on:mousemove={handleMouseMovePan}
					on:mouseup={handleMouseUpPan}
				>
					<!-- SVG pour les connexions entre nœuds -->
					<svg class="connections-svg" id="{elem_id}-connections-svg">
						<!-- Connexions permanentes -->
						{#each connections as conn, i}
							{@const fromNode = nodes[conn.from]}
							{@const toNode = nodes[conn.to]}
							{#if fromNode && toNode}
								{@const fromNodeElement =
									typeof document !== "undefined"
										? document.getElementById(
												`${elem_id}-node-${conn.from}`,
											)
										: null}
								{@const toNodeElement =
									typeof document !== "undefined"
										? document.getElementById(
												`${elem_id}-node-${conn.to}`,
											)
										: null}
								{@const fromNodeHeight = fromNodeElement
									? fromNodeElement.offsetHeight
									: 30}
								{@const toNodeHeight = toNodeElement
									? toNodeElement.offsetHeight
									: 30}
								<path
									id="{elem_id}-connection-{i}"
									class="connection-path"
									d={createCurvedPath(
										fromNode.x +
											(fromNode.type === "email"
												? 40
												: 100) +
											offset.x,
										fromNode.y +
											fromNodeHeight / 2 +
											offset.y,
										toNode.x + offset.x,
										toNode.y + toNodeHeight / 2 + offset.y,
									)}
									stroke="#666"
									stroke-width="2"
									fill="none"
								/>
							{/if}
						{/each}

						<!-- Connexion temporaire en cours de création -->
						{#if tempConnection}
							<path
								id="{elem_id}-temp-connection"
								class="temp-connection-path"
								d={createCurvedPath(
									tempConnection.from.x + offset.x,
									tempConnection.from.y + offset.y,
									tempConnection.to.x + offset.x,
									tempConnection.to.y + offset.y,
								)}
								stroke="#999"
								stroke-width="2"
								stroke-dasharray="5,5"
								fill="none"
							/>
						{/if}
					</svg>

					<!-- Rendu des nœuds dans le workflow -->
					{#each nodes as node, i}
						<!-- Nœud Email spécial (plus petit) -->
						{#if node.type === "email"}
							<div
								class="workflow-node email-node {node.statut ===
								'active'
									? 'active'
									: ''}"
								id="{elem_id}-node-{i}"
								data-type="node"
								role="button"
								tabindex="0"
								aria-label="Nœud email - {node.label}"
								style="left:{node.x + offset.x}px; top:{node.y +
									offset.y}px; border:{connectionStart === i
									? '2px solid #007acc'
									: '1px solid #ccc'}"
								on:mousedown={(e) => handleNodeMouseDown(e, i)}
								on:keydown={(e) => {
									if (e.key === "Enter" || e.key === " ") {
										e.preventDefault();
										// Optionally trigger node selection or action
									}
								}}
							>
								<!-- Spinner pour statut actif -->
								{#if node.statut === "active"}
									<div class="node-spinner"></div>
								{/if}

								<!-- Bouton de suppression -->
								<button
									class="delete-button"
									id="{elem_id}-delete-button-{i}"
									on:click|stopPropagation={() =>
										deleteNode(i)}
									aria-label="Supprimer le nœud email"
									title="Supprimer le nœud">×</button
								>

								<!-- Bouton de configuration email -->
								<button
									class="config-email-button"
									id="{elem_id}-config-button-{i}"
									on:click|stopPropagation={(e) =>
										handleEmailConfigClick(e, i)}
									aria-label="Configurer le nœud email"
									title="Configurer les destinataires"
									>⚙</button
								>

								<!-- Input connector: visible uniquement en mode connexion -->
								{#if isConnecting}
									<div
										class="connector input-connector"
										id="{elem_id}-input-connector-{i}"
										role="button"
										tabindex="0"
										aria-label="Point de connexion d'entrée"
										on:mouseup={(e) => endConnection(e, i)}
										on:keydown={(e) => {
											if (
												e.key === "Enter" ||
												e.key === " "
											) {
												e.preventDefault();
												endConnection(e, i);
											}
										}}
									></div>
								{/if}

								<!-- Logo Gmail -->
								<img
									src="https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg"
									alt="Gmail"
									class="email-node-icon"
								/>

								<!-- Output connector (point de sortie) -->
								<div
									class="connector output-connector"
									id="{elem_id}-output-connector-{i}"
									role="button"
									tabindex="0"
									aria-label="Point de connexion de sortie"
									on:mousedown={(e) => startConnection(e, i)}
									on:mouseenter={(e) =>
										(e.currentTarget.style.opacity = "1")}
									on:mouseleave={(e) =>
										(e.currentTarget.style.opacity = "0")}
									on:keydown={(e) => {
										if (
											e.key === "Enter" ||
											e.key === " "
										) {
											e.preventDefault();
											startConnection(e, i);
										}
									}}
									style="opacity:0"
								></div>
							</div>

							<!-- Nœud normal (agent standard) -->
						{:else}
							<div
								class="workflow-node {node.statut === 'active'
									? 'active'
									: ''}"
								id="{elem_id}-node-{i}"
								data-type="node"
								role="button"
								tabindex="0"
								aria-label="Nœud - {node.label}"
								style="left:{node.x + offset.x}px; top:{node.y +
									offset.y}px; border:{connectionStart === i
									? '2px solid #007acc'
									: '1px solid #999'}"
								on:mousedown={(e) => handleNodeMouseDown(e, i)}
								on:keydown={(e) => {
									if (e.key === "Enter" || e.key === " ") {
										e.preventDefault();
										// Optionally trigger node selection or action
									}
								}}
							>
								<!-- Spinner pour statut actif -->
								{#if node.statut === "active"}
									<div class="node-spinner"></div>
								{/if}

								<!-- Bouton de suppression -->
								<button
									class="delete-button"
									id="{elem_id}-delete-button-{i}"
									on:click|stopPropagation={() =>
										deleteNode(i)}
									aria-label="Supprimer le nœud {node.label}"
									title="Supprimer le nœud">×</button
								>

								<!-- Input connector: visible uniquement en mode connexion -->
								{#if isConnecting}
									<div
										class="connector input-connector"
										id="{elem_id}-input-connector-{i}"
										role="button"
										tabindex="0"
										aria-label="Point de connexion d'entrée"
										on:mouseup={(e) => endConnection(e, i)}
										on:keydown={(e) => {
											if (
												e.key === "Enter" ||
												e.key === " "
											) {
												e.preventDefault();
												endConnection(e, i);
											}
										}}
									></div>
								{/if}

								<!-- Libellé du nœud -->
								<span
									class="node-label"
									id="{elem_id}-node-label-{i}"
									>{node.label}</span
								>

								<!-- Output connector (point de sortie) -->
								<div
									class="connector output-connector"
									id="{elem_id}-output-connector-{i}"
									role="button"
									tabindex="0"
									aria-label="Point de connexion de sortie"
									on:mousedown={(e) => startConnection(e, i)}
									on:mouseenter={(e) =>
										(e.currentTarget.style.opacity = "1")}
									on:mouseleave={(e) =>
										(e.currentTarget.style.opacity = "0")}
									on:keydown={(e) => {
										if (
											e.key === "Enter" ||
											e.key === " "
										) {
											e.preventDefault();
											startConnection(e, i);
										}
									}}
									style="opacity:0"
								></div>
							</div>
						{/if}
					{/each}
				</div>
			</div>
		</div>
	</div>
</Block>

<!-- Styles CSS du composant -->

<style>
	/* Conteneur principal du composant */
	.canvas-workflow-container {
		width: 100%;
		height: 600px;
		border: 1px solid #ddd;
		border-radius: 6px;
		overflow: hidden;
	}
	/* Layout principal en flex */
	.workflow-main {
		display: flex;
		height: 100%;
	}
	/* Panneau latéral des agents */
	.agents-list {
		width: 200px;
		border-right: 1px solid #ddd;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
	}
	.agents-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px;
		border-bottom: 1px solid #ddd;
		background: #f5f5f5;
		min-height: 40px;
		box-sizing: border-box;
	}
	.agents-header h3 {
		margin: 0;
	}
	/* Conteneur des agents draggables */
	.boxes-container {
		display: flex;
		flex-direction: column;
		gap: 4px;
		padding: 8px;
		flex: 1;
	}
	.draggable-box {
		padding: 8px;
		border-radius: 6px;
		cursor: grab;
		user-select: none;
		border: 1px solid #ccc;
		background: #f9f9f9;
	}
	/* Zone principale du workflow */
	.workflow-canvas {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: #f5f5f5;
	}
	.workflow-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-left: 3px;
		border-bottom: 1px solid #ddd;
		background: #f5f5f5;
		min-height: 40px;
		box-sizing: border-box;
	}
	.workflow-header h3 {
		margin: 0;
	}
	/* Zone de dessin interactive */
	.canvas-area {
		flex: 1;
		position: relative;
		cursor: grab;
		overflow: hidden;
		background: radial-gradient(#ccc 1px, transparent 1px);
		background-size: 20px 20px;
	}
	/* SVG pour les connexions */
	.connections-svg {
		position: absolute;
		width: 100%;
		height: 100%;
		top: 0;
		left: 0;
		pointer-events: none;
		z-index: 1;
	}
	/* Nœuds du workflow */
	.workflow-node {
		position: absolute;
		width: 100px;
		padding: 6px 10px;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: grab;
		user-select: none;
		z-index: 2;
		min-width: 100px;
		text-align: center;
		background: #f0f0f0;
		color: #333;
	}
	.node-label {
		font-size: 12px;
		font-weight: 500;
	}
	/* Boutons des nœuds */
	.delete-button {
		position: absolute;
		top: -2px;
		right: -2px;
		width: 18px;
		height: 18px;
		border: none;
		border-radius: 50%;
		background: none;
		color: #999;
		font-size: 14px;
		font-weight: bold;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 4;
	}
	.config-email-button {
		position: absolute;
		top: -5px;
		left: -5px;
		width: 16px;
		height: 16px;
		border: none;
		border-radius: 50%;
		background: #4285f4;
		color: white;
		font-size: 10px;
		font-weight: bold;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 4;
	}
	/* Points de connexion */
	.connector {
		position: absolute;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: 2px solid white;
		background: #666;
		cursor: crosshair;
		z-index: 3;
		transition: all 0.2s ease;
	}
	.input-connector {
		left: -6px;
		top: 50%;
		transform: translateY(-50%);
	}
	.output-connector {
		right: -6px;
		top: 50%;
		transform: translateY(-50%);
	}
	/* Styles des connexions */
	.connection-path {
		stroke: #666;
	}
	.temp-connection-path {
		stroke: #999;
	}

	/* Bouton Email en haut à droite */
	.email-button {
		width: 32px;
		height: 32px;
		border-radius: 6px;
		cursor: grab;
		user-select: none;
		border: 1px solid #ddd;
		background: #f9f9f9;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-right: 3px;
	}
	.email-button-icon {
		width: 20px;
		height: 20px;
	}

	/* Nœud Email spécial dans le workflow */
	.email-node {
		width: 40px !important;
		height: 40px !important;
		min-width: 40px !important;
		border-radius: 6px;
		background: white !important;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
	}
	.email-node-icon {
		width: 28px;
		height: 28px;
	}

	/* Menu de configuration Email (popup) */
	.email-config-panel {
		position: absolute;
		top: 8px;
		right: 8px;
		width: 300px;
		background: white;
		border: 1px solid #ddd;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 10;
	}
	.email-config-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px 16px;
		border-bottom: 1px solid #eee;
		background: #f8f9fa;
		border-radius: 8px 8px 0 0;
	}
	.email-config-header h4 {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
		color: #333;
	}
	.close-config-button {
		background: none;
		border: none;
		font-size: 18px;
		color: #666;
		cursor: pointer;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
	}
	/* Contenu de la configuration email */
	.email-config-content {
		padding: 16px;
	}
	.email-config-content label {
		display: block;
		margin-bottom: 12px;
		font-size: 12px;
		font-weight: 500;
		color: #555;
	}
	/* Champs de destinataires */
	.recipient-field-container {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 8px;
	}
	.recipient-input {
		flex: 1;
		border: 1px solid #ddd;
		border-radius: 4px;
		padding: 8px;
		font-size: 12px;
		font-family: inherit;
		box-sizing: border-box;
	}
	.recipient-input::placeholder {
		font-style: italic;
		font-weight: 200;
		color: #999;
	}
	.recipient-input:focus {
		outline: none;
		border-color: #4285f4;
		box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
	}
	.remove-recipient-button {
		width: 18px;
		height: 18px;
		border: none;
		border-radius: 50%;
		background: none;
		color: #999;
		font-size: 14px;
		font-weight: bold;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 4;
	}
	/* Boutons d'action */
	.add-recipient-button {
		padding: 8px 12px;
		border-radius: 4px;
		cursor: pointer;
		font-size: 30px;
		font-weight: 500;
		width: 100%;
		margin-bottom: 12px;
	}
	.email-config-buttons {
		display: flex;
		gap: 8px;
		margin-top: 12px;
		justify-content: flex-end;
	}

	.btn-save {
		width: 100px;
		padding: 6px 10px;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		z-index: 2;
		text-align: center;
		background: #f0f0f0;
		color: #333;
	}
	.btn-save {
		color: #999;
	}

	/* Spinner pour les nœuds actifs */
	.node-spinner {
		position: absolute;
		bottom: -6px;
		left: -6px;
		width: 16px;
		height: 16px;
		border: 2px solid #333;
		border-top: 2px solid #999;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		z-index: 5;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	/* Effet blur pour les nœuds actifs */
	.workflow-node.active {
		opacity: 0.5;
		transition:
			filter 0.3s ease,
			opacity 0.3s ease;
	}
</style>
