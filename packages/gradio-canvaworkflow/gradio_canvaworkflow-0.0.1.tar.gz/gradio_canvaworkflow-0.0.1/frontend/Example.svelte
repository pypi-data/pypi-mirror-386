<script lang="ts">
	export let value: {nodes?: any[], connections?: any[]} | null;
	export let type: "gallery" | "table";
	export let selected = false;
</script>

<div 
	class="example-container"
	class:selected
	class:table={type === "table"}
	class:gallery={type === "gallery"}
>
	{#if value && value.nodes}
		<div class="example-preview">
			<div class="mini-canvas">
				{#each value.nodes as node}
					<div 
						class="mini-node"
						style="left: {(node.x || 0) / 4}px; top: {(node.y || 0) / 4}px; background-color: {node.color || '#007acc'};"
					>
						{node.label}
					</div>
				{/each}
				
				{#each (value.connections || []) as connection}
					{@const fromNode = value.nodes[connection.from]}
					{@const toNode = value.nodes[connection.to]}
					{#if fromNode && toNode}
						<svg class="mini-connection">
							<line
								x1={(fromNode.x || 0) / 4 + 20}
								y1={(fromNode.y || 0) / 4 + 10}
								x2={(toNode.x || 0) / 4}
								y2={(toNode.y || 0) / 4 + 10}
								stroke="#007acc"
								stroke-width="1"
							/>
						</svg>
					{/if}
				{/each}
			</div>
			<div class="example-info">
				{value.nodes.length} nodes, {(value.connections || []).length} connections
			</div>
		</div>
	{:else}
		<div class="empty-example">Empty workflow</div>
	{/if}
</div>

<style>
	.example-container {
		border: 1px solid var(--input-border-color);
		border-radius: 4px;
		padding: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.example-container:hover {
		border-color: var(--input-border-color-focus);
		background: var(--background-fill-secondary);
	}

	.example-container.selected {
		border-color: var(--input-border-color-focus);
		background: var(--background-fill-secondary);
		box-shadow: 0 0 0 1px var(--input-border-color-focus);
	}

	.gallery {
		padding: var(--size-1) var(--size-2);
	}

	.example-preview {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.mini-canvas {
		position: relative;
		width: 120px;
		height: 80px;
		background: var(--input-background-fill);
		border-radius: 2px;
		overflow: hidden;
	}

	.mini-node {
		position: absolute;
		width: 35px;
		height: 15px;
		background: #007acc;
		border-radius: 2px;
		font-size: 8px;
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.mini-connection {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.example-info {
		font-size: 10px;
		color: var(--body-text-color-subdued);
		text-align: center;
	}

	.empty-example {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 60px;
		color: var(--body-text-color-subdued);
		font-size: 12px;
	}
</style>