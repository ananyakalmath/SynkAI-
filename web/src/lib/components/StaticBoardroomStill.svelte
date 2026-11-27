<script lang="ts">
	let { caption = 'A still of the SynkAI boardroom' }: { caption?: string } = $props();

	const windowIndices = Array.from({ length: 26 }, (_, i) => i);
</script>

<figure class="still">
	<svg viewBox="0 0 1200 675" role="img" aria-labelledby="still-title" class="still-svg">
		<title id="still-title">{caption}</title>
		<defs>
			<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#15181d" />
				<stop offset="100%" stop-color="#07080a" />
			</linearGradient>
			<linearGradient id="skyline" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#0c0e12" />
				<stop offset="100%" stop-color="#07080a" />
			</linearGradient>
		</defs>

		<rect width="1200" height="675" fill="#07080a" />
		<rect x="860" width="340" height="675" fill="url(#skyline)" />

		{#each windowIndices as i (i)}
			<rect
				x={880 + (i % 7) * 44}
				y={60 + Math.floor(i / 7) * 110}
				width="22"
				height="32"
				fill="#f0d9a8"
				opacity={0.18 + ((i * 7) % 10) / 22}
			/>
		{/each}

		<polygon points="180,520 1020,520 860,300 340,300" fill="url(#floor)" />
		<polygon
			points="300,330 900,330 860,300 340,300"
			fill="#1a1d22"
			stroke="#c9a467"
			stroke-width="2"
		/>

		<ellipse
			cx="600"
			cy="300"
			rx="190"
			ry="46"
			fill="none"
			stroke="#5fe1e0"
			stroke-width="2"
			opacity="0.55"
		/>
		<text
			x="600"
			y="246"
			text-anchor="middle"
			fill="#5fe1e0"
			font-size="13"
			letter-spacing="2"
			opacity="0.8"
		>
			BEFORE · DURING · AFTER · FOLLOW-THROUGH · NEXT MEETING
		</text>

		{#each [240, 340, 440, 540] as x (x)}
			<rect {x} y="410" width="34" height="46" fill="#1e2229" />
			<rect {x} y="470" width="34" height="34" fill="#15181d" />
		{/each}
		{#each [660, 760, 860, 960] as x (x)}
			<rect {x} y="410" width="34" height="46" fill="#1e2229" />
			<rect {x} y="470" width="34" height="34" fill="#15181d" />
		{/each}
	</svg>
	<figcaption class="illustrative-note">illustrative still — not a live render</figcaption>
</figure>

<style>
	.still {
		margin: 0;
		position: relative;
	}

	.still-svg {
		display: block;
		width: 100%;
		height: auto;
		border: 1px solid var(--color-graphite-2);
		border-radius: 10px;
	}

	figcaption {
		margin-top: 0.6rem;
		text-align: center;
	}
</style>
