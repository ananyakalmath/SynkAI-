<script lang="ts">
	import DoorsSection from '#lib/components/DoorsSection.svelte';
	import RoomJourney from '#lib/components/RoomJourney.svelte';
	import UnderTheHoodSection from '#lib/components/UnderTheHoodSection.svelte';
	import CTASection from '#lib/components/CTASection.svelte';
	import Footer from '#lib/components/Footer.svelte';
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
</script>

<DoorsSection />
<RoomJourney />
<UnderTheHoodSection />
<CTASection {form} />
<Footer />
