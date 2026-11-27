<script lang="ts">
	import { footer, product } from '#lib/content.js';
</script>

<footer class="footer">
	<div class="footer-inner">
		<p class="footer-wordmark">{footer.wordmark}</p>
		<div class="footer-row">
			<p class="footer-note">{footer.note}</p>
			<nav class="footer-links" aria-label="Footer">
				{#each footer.links as link (link.label)}
					<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- placeholder anchor, not a SvelteKit route -->
					<a href={link.href}>{link.label}</a>
				{/each}
			</nav>
		</div>
		<p class="footer-status">{product.status}</p>
	</div>
</footer>

<style>
	.footer {
		background: var(--color-obsidian);
		border-top: 1px solid var(--color-graphite-2);
		padding: clamp(3rem, 8vw, 5rem) clamp(1.25rem, 5vw, 4rem) clamp(2rem, 5vw, 3rem);
	}

	.footer-inner {
		max-width: 1200px;
		margin: 0 auto;
	}

	.footer-wordmark {
		font-family: var(--font-display);
		font-size: clamp(3.5rem, 14vw, 9rem);
		line-height: 0.9;
		letter-spacing: -0.03em;
		color: var(--color-ivory);
	}

	.footer-row {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 1.5rem;
		margin-top: 1.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--color-graphite-2);
	}

	.footer-note {
		color: var(--color-ivory-faint);
		font-size: 0.85rem;
		max-width: 32rem;
	}

	.footer-links {
		display: flex;
		gap: 1.25rem;
	}

	.footer-links a {
		font-size: 0.85rem;
		color: var(--color-ivory-dim);
		text-decoration: none;
	}

	.footer-links a:hover {
		color: var(--color-brass);
	}

	.footer-status {
		margin-top: 1.5rem;
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--color-ivory-faint);
		max-width: 38rem;
	}
</style>
