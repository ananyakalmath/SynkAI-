import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { clamp01, smoothstep } from '#lib/motion/easing.js';

const COLOR = {
	obsidian: 0x07080a,
	// the CSS palette's graphite/table tones are near-black in sRGB and would
	// decode to almost-zero linear albedo — barely readable under any amount
	// of light. These 3D-only tones are lifted so the room actually reads as
	// lit; the dark mood comes from the lighting and tone mapping instead.
	graphite: 0x6b7078,
	graphite2: 0x7a8088,
	tableTop: 0x454b54,
	brass: 0xc9a467,
	signal: 0x5fe1e0,
	ivory: 0xf3efe6,
	windowWarm: 0xf0d9a8
};

function lerp(a: number, b: number, t: number) {
	return a + (b - a) * t;
}

type Vec3 = [number, number, number];

interface CameraKey {
	p: number;
	pos: Vec3;
	look: Vec3;
}

// camera path along the room's z axis (table runs roughly z -6.5 .. 6.5).
// progress 0→1 drives everything below; nothing here plays on a clock.
const CAMERA_KEYS: CameraKey[] = [
	{ p: 0.0, pos: [0, 1.7, -7.4], look: [0, 1.5, -2.2] },
	{ p: 0.16, pos: [0, 1.68, 0.8], look: [0, 1.3, 4.2] },
	{ p: 0.26, pos: [0, 1.5, 2.3], look: [0, 0.8, 3.1] },
	{ p: 0.5, pos: [0, 1.42, 3.9], look: [0, 0.82, 4.6] },
	{ p: 0.8, pos: [0, 1.4, 5.5], look: [0, 0.82, 6.2] },
	{ p: 0.92, pos: [0.6, 4.4, -5.2], look: [0, 0.9, 2.2] },
	{ p: 1.0, pos: [1.1, 4.9, -6.4], look: [0, 1.05, 1.2] }
];

function cameraPose(p: number) {
	const clamped = clamp01(p);
	let i = 0;
	while (i < CAMERA_KEYS.length - 2 && clamped > CAMERA_KEYS[i + 1].p) i++;
	const a = CAMERA_KEYS[i];
	const b = CAMERA_KEYS[i + 1];
	const span = b.p - a.p || 1;
	const t = smoothstep(0, 1, clamp01((clamped - a.p) / span));
	const pos: Vec3 = [
		lerp(a.pos[0], b.pos[0], t),
		lerp(a.pos[1], b.pos[1], t),
		lerp(a.pos[2], b.pos[2], t)
	];
	const look: Vec3 = [
		lerp(a.look[0], b.look[0], t),
		lerp(a.look[1], b.look[1], t),
		lerp(a.look[2], b.look[2], t)
	];
	return { pos, look };
}

function drawHologramTexture(): HTMLCanvasElement {
	const canvas = document.createElement('canvas');
	canvas.width = 1024;
	canvas.height = 1024;
	const ctx = canvas.getContext('2d')!;
	const cx = 512;
	const cy = 512;
	const r = 360;

	ctx.clearRect(0, 0, 1024, 1024);

	// a soft glow disc first — additive blending on thin strokes alone reads
	// as almost nothing at this mesh's screen size, so give it real area.
	// text is deliberately left out: a flat ground-plane texture reads
	// mirrored or upside down depending on which way the camera looks down
	// at it, but a ring/segments/dots read identically either way — the
	// stage labels themselves are already shown correctly by the HTML overlay
	const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 1.15);
	glow.addColorStop(0, 'rgba(95, 225, 224, 0.07)');
	glow.addColorStop(0.7, 'rgba(95, 225, 224, 0.025)');
	glow.addColorStop(1, 'rgba(95, 225, 224, 0)');
	ctx.fillStyle = glow;
	ctx.fillRect(0, 0, 1024, 1024);

	ctx.strokeStyle = 'rgba(95, 225, 224, 0.5)';
	ctx.lineWidth = 4;
	ctx.beginPath();
	ctx.arc(cx, cy, r, 0, Math.PI * 2);
	ctx.stroke();

	const segmentCount = 5;
	const segment = (Math.PI * 2) / segmentCount;

	for (let index = 0; index < segmentCount; index++) {
		const start = -Math.PI / 2 + index * segment;
		const end = start + segment * 0.82;
		ctx.strokeStyle = 'rgba(95, 225, 224, 0.6)';
		ctx.lineWidth = 7;
		ctx.beginPath();
		ctx.arc(cx, cy, r, start, end);
		ctx.stroke();

		const mid = (start + end) / 2;
		const dotX = cx + Math.cos(mid) * r;
		const dotY = cy + Math.sin(mid) * r;
		ctx.fillStyle = 'rgba(243, 239, 230, 0.85)';
		ctx.beginPath();
		ctx.arc(dotX, dotY, 8, 0, Math.PI * 2);
		ctx.fill();
	}

	ctx.fillStyle = 'rgba(95, 225, 224, 0.9)';
	ctx.beginPath();
	ctx.arc(cx, cy, 6, 0, Math.PI * 2);
	ctx.fill();

	return canvas;
}

export interface BoardroomHandle {
	setProgress(p: number): void;
	resize(width: number, height: number): void;
	setRunning(running: boolean): void;
	dispose(): void;
}

export function createBoardroomScene(canvas: HTMLCanvasElement, mobile: boolean): BoardroomHandle {
	const renderer = new THREE.WebGLRenderer({
		canvas,
		antialias: !mobile,
		powerPreference: 'high-performance'
	});
	renderer.setClearColor(COLOR.obsidian, 1);
	renderer.toneMapping = THREE.ACESFilmicToneMapping;
	renderer.toneMappingExposure = 0.95;
	const dprCap = mobile ? 1.25 : 1.75;
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, dprCap));

	const scene = new THREE.Scene();
	scene.fog = new THREE.Fog(COLOR.obsidian, 6, 22);

	const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 60);

	// physically-based lighting needs much higher intensities than the old
	// unitless scale — these values are tuned by eye, not by lux
	const ambient = new THREE.AmbientLight(0x4a4e58, 2.1);
	scene.add(ambient);

	const hemi = new THREE.HemisphereLight(0x5a5e68, 0x07080a, 1.2);
	scene.add(hemi);

	const rimLight = new THREE.DirectionalLight(COLOR.windowWarm, 1);
	rimLight.position.set(9, 6, 0);
	scene.add(rimLight);

	// table — stone plinth + slab top with a brass trim line
	const tableGroup = new THREE.Group();
	const plinth = new THREE.Mesh(
		new THREE.BoxGeometry(1.7, 0.7, 12.6),
		new THREE.MeshStandardMaterial({ color: COLOR.graphite, roughness: 0.75, metalness: 0.1 })
	);
	plinth.position.set(0, 0.35, 0);
	tableGroup.add(plinth);

	const slab = new THREE.Mesh(
		new THREE.BoxGeometry(2.05, 0.07, 13),
		// kept close to dielectric — true PBR metals go near-black without an
		// environment map to reflect, which this lightweight scene doesn't have
		new THREE.MeshStandardMaterial({ color: COLOR.tableTop, roughness: 0.45, metalness: 0.15 })
	);
	slab.position.set(0, 0.74, 0);
	tableGroup.add(slab);

	const trim = new THREE.Mesh(
		new THREE.BoxGeometry(2.08, 0.015, 13.02),
		new THREE.MeshStandardMaterial({ color: COLOR.brass, roughness: 0.4, metalness: 0.25 })
	);
	trim.position.set(0, 0.705, 0);
	tableGroup.add(trim);

	scene.add(tableGroup);

	// chairs — instanced boxes abstracted into seat + back silhouettes
	const chairPairs = mobile ? 4 : 7;
	const chairSpacing = 11.5 / Math.max(chairPairs - 1, 1);
	const seatGeo = new THREE.BoxGeometry(0.62, 0.08, 0.62);
	const backGeo = new THREE.BoxGeometry(0.62, 0.7, 0.08);
	const chairMat = new THREE.MeshStandardMaterial({
		color: COLOR.graphite2,
		roughness: 0.6,
		metalness: 0.15
	});
	const seatMesh = new THREE.InstancedMesh(seatGeo, chairMat, chairPairs * 2);
	const backMesh = new THREE.InstancedMesh(backGeo, chairMat, chairPairs * 2);

	const dummy = new THREE.Object3D();
	let instanceIndex = 0;
	for (let i = 0; i < chairPairs; i++) {
		const z = -5.75 + i * chairSpacing;
		for (const side of [-1, 1]) {
			const x = side * 1.55;
			dummy.position.set(x, 0.42, z);
			dummy.rotation.y = 0;
			dummy.updateMatrix();
			seatMesh.setMatrixAt(instanceIndex, dummy.matrix);

			dummy.position.set(x, 0.72, z + side * -0.28);
			dummy.updateMatrix();
			backMesh.setMatrixAt(instanceIndex, dummy.matrix);
			instanceIndex++;
		}
	}
	scene.add(seatMesh, backMesh);

	// ceiling light strips — turn on sequentially during the walk-in
	const stripCount = mobile ? 4 : 7;
	const stripSpacing = 12 / Math.max(stripCount - 1, 1);
	const ceilingLights: { mesh: THREE.Mesh; light: THREE.PointLight; z: number }[] = [];
	for (let i = 0; i < stripCount; i++) {
		const z = -6 + i * stripSpacing;
		const mat = new THREE.MeshStandardMaterial({
			color: COLOR.ivory,
			emissive: COLOR.ivory,
			emissiveIntensity: 0
		});
		const mesh = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.06, 1.7), mat);
		mesh.position.set(0, 3.5, z);
		scene.add(mesh);

		const light = new THREE.PointLight(COLOR.windowWarm, 0, 11, 2.2);
		light.position.set(0, 3.3, z);
		scene.add(light);

		ceilingLights.push({ mesh, light, z });
	}

	// glass wall skyline — instanced warm windows, static (no per-frame cost)
	const windowCount = mobile ? 60 : 160;
	const windowGeo = new THREE.PlaneGeometry(0.22, 0.32);
	const windowMat = new THREE.MeshBasicMaterial({
		color: COLOR.windowWarm,
		transparent: true,
		toneMapped: false
	});
	const windowMesh = new THREE.InstancedMesh(windowGeo, windowMat, windowCount);
	const windowColor = new THREE.Color();
	for (let i = 0; i < windowCount; i++) {
		const x = 9.2;
		const y = 0.6 + Math.random() * 9.5;
		const z = -9 + Math.random() * 18;
		dummy.position.set(x, y, z);
		dummy.rotation.set(0, -Math.PI / 2, 0);
		dummy.scale.setScalar(0.6 + Math.random() * 0.8);
		dummy.updateMatrix();
		windowMesh.setMatrixAt(i, dummy.matrix);
		const brightness = 0.25 + Math.random() * 0.75;
		windowColor.setRGB(brightness, brightness * 0.9, brightness * 0.65);
		windowMesh.setColorAt(i, windowColor);
	}
	windowMesh.instanceColor!.needsUpdate = true;
	scene.add(windowMesh);

	const glassWall = new THREE.Mesh(
		new THREE.PlaneGeometry(20, 11),
		new THREE.MeshBasicMaterial({ color: 0x0a0c10, transparent: true, opacity: 0.18 })
	);
	glassWall.position.set(9.05, 5, 0);
	glassWall.rotation.y = -Math.PI / 2;
	scene.add(glassWall);

	// hologram — canvas-texture ring above the table
	const hologramTexture = new THREE.CanvasTexture(drawHologramTexture());
	hologramTexture.colorSpace = THREE.SRGBColorSpace;
	const hologramMat = new THREE.MeshBasicMaterial({
		map: hologramTexture,
		transparent: true,
		opacity: 0,
		blending: THREE.AdditiveBlending,
		depthWrite: false,
		toneMapped: false
	});
	// flat on the table, facing straight up — a tilted "HUD" version mirrored
	// its text depending on viewing side, so this stays simple and reliable
	const hologramMesh = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 3.6), hologramMat);
	hologramMesh.rotation.x = -Math.PI / 2;
	hologramMesh.position.set(0, 0.85, 3.2);
	scene.add(hologramMesh);

	const hologramLight = new THREE.PointLight(COLOR.signal, 0, 5, 1.4);
	hologramLight.position.set(0, 1.4, 3.4);
	scene.add(hologramLight);

	// postprocessing — a restrained bloom so only emissive/signal elements glow
	const composer = new EffectComposer(renderer);
	composer.addPass(new RenderPass(scene, camera));
	const bloomPass = new UnrealBloomPass(new THREE.Vector2(1, 1), mobile ? 0.35 : 0.5, 0.5, 0.85);
	composer.addPass(bloomPass);
	composer.addPass(new OutputPass());

	let running = false;
	let rafId = 0;

	function applyProgress(p: number) {
		const { pos, look } = cameraPose(p);
		camera.position.set(pos[0], pos[1], pos[2]);
		camera.lookAt(look[0], look[1], look[2]);

		// ceiling lights switch on as the camera passes them during the walk-in,
		// stay lit through the beats, dim for the pull-back, then partially return
		const walkIn = smoothstep(0.0, 0.16, p);
		const pullBackDim = 1 - smoothstep(0.8, 0.9, p) * 0.75;
		const pullBackReturn = pullBackDim + smoothstep(0.92, 1.0, p) * 0.2;
		for (const strip of ceilingLights) {
			const reach = smoothstep(strip.z - 6.5, strip.z - 3.2, pos[2]);
			const base = Math.max(walkIn > 0.02 ? reach : 0, p > 0.16 ? 1 : 0);
			const final = base * Math.min(pullBackReturn, 1);
			(strip.mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = final * 1.6;
			strip.light.intensity = final * 6;
		}

		// hologram fades in once the table "comes alive", fades before the wide pull-back
		const hologramIn = smoothstep(0.1, 0.18, p);
		const hologramOut = 1 - smoothstep(0.86, 0.94, p);
		const hologramOpacity = Math.min(hologramIn, hologramOut) * 0.7;
		hologramMat.opacity = hologramOpacity;
		hologramLight.intensity = hologramOpacity * 0.3;
	}

	function resize(width: number, height: number) {
		camera.aspect = width / height;
		camera.updateProjectionMatrix();
		renderer.setSize(width, height, false);
		composer.setSize(width, height);
	}

	function render() {
		rafId = requestAnimationFrame(render);
		composer.render();
	}

	function setRunning(next: boolean) {
		if (next === running) return;
		running = next;
		if (running) {
			render();
		} else {
			cancelAnimationFrame(rafId);
		}
	}

	function dispose() {
		setRunning(false);
		scene.traverse((object: THREE.Object3D) => {
			if (object instanceof THREE.Mesh || object instanceof THREE.InstancedMesh) {
				(object.geometry as THREE.BufferGeometry).dispose();
				const material = object.material as THREE.Material | THREE.Material[];
				if (Array.isArray(material)) material.forEach((m: THREE.Material) => m.dispose());
				else material.dispose();
			}
		});
		hologramTexture.dispose();
		composer.dispose();
		renderer.dispose();
	}

	applyProgress(0);

	return { setProgress: applyProgress, resize, setRunning, dispose };
}
