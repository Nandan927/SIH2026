import * as THREE from 'three';

(() => {
  'use strict';

  // ═══════════════════════════════════════════════════════════
  //  Renderer & scene setup
  // ═══════════════════════════════════════════════════════════
  const canvas = document.getElementById('scene');
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0, 6);

  // ═══════════════════════════════════════════════════════════
  //  Lighting
  // ═══════════════════════════════════════════════════════════
  scene.add(new THREE.AmbientLight(0xffffff, 1.0));

  const lightY = new THREE.PointLight(0xf59e0b, 1.1, 30, 2);
  lightY.position.set(3, 3, 4);
  scene.add(lightY);

  const lightO = new THREE.PointLight(0xea580c, 0.9, 30, 2);
  lightO.position.set(-3.5, -2, 3);
  scene.add(lightO);

  // ═══════════════════════════════════════════════════════════
  //  Root group & Geometries
  // ═══════════════════════════════════════════════════════════
  const root = new THREE.Group();
  root.scale.setScalar(0.7);
  scene.add(root);

  // Outer wireframe
  const outerGeo = new THREE.IcosahedronGeometry(1.9, 1);
  const outerWire = new THREE.LineSegments(
    new THREE.WireframeGeometry(outerGeo),
    new THREE.LineBasicMaterial({
      color: 0xd97706,
      transparent: true,
      opacity: 0.55,
    })
  );
  root.add(outerWire);

  // Inner wireframe
  const innerGeo = new THREE.IcosahedronGeometry(1.35, 0);
  const innerWire = new THREE.LineSegments(
    new THREE.WireframeGeometry(innerGeo),
    new THREE.LineBasicMaterial({
      color: 0xea580c,
      transparent: true,
      opacity: 0.85,
    })
  );
  root.add(innerWire);

  // ═══════════════════════════════════════════════════════════
  //  Skill-node network
  // ═══════════════════════════════════════════════════════════
  const positions = outerGeo.attributes.position;
  const uniqueVerts = [];
  const seen = new Set();
  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i);
    const y = positions.getY(i);
    const z = positions.getZ(i);
    const key = `${x.toFixed(3)}|${y.toFixed(3)}|${z.toFixed(3)}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueVerts.push(new THREE.Vector3(x, y, z));
    }
  }

  const edgePositions = [];
  for (let i = 0; i < uniqueVerts.length; i++) {
    const v = uniqueVerts[i];
    const near = [];
    for (let j = 0; j < uniqueVerts.length; j++) {
      if (i === j) continue;
      near.push({ idx: j, d: v.distanceToSquared(uniqueVerts[j]) });
    }
    near.sort((a, b) => a.d - b.d);

    for (let k = 0; k < Math.min(3, near.length); k++) {
      const j = near[k].idx;
      if (i < j) {
        const u = uniqueVerts[j];
        edgePositions.push(v.x, v.y, v.z, u.x, u.y, u.z);
      }
    }
  }

  const networkGeo = new THREE.BufferGeometry();
  networkGeo.setAttribute('position', new THREE.Float32BufferAttribute(edgePositions, 3));
  const network = new THREE.LineSegments(
    networkGeo,
    new THREE.LineBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0.75,
    })
  );
  root.add(network);

  // Dynamic texture generator
  function makeDotTexture() {
    const size = 64;
    const c = document.createElement('canvas');
    c.width = c.height = size;
    const ctx = c.getContext('2d');
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    g.addColorStop(0.00, 'rgba(255, 255, 255, 1)');
    g.addColorStop(0.25, 'rgba(255, 226, 178, 1)');
    g.addColorStop(0.55, 'rgba(245, 158, 11, 0.95)');
    g.addColorStop(0.85, 'rgba(234, 88, 12, 0.55)');
    g.addColorStop(1.00, 'rgba(234, 88, 12, 0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  }
  const dotTex = makeDotTexture();

  // Nodes
  const nodePositions = [];
  for (const v of uniqueVerts) {
    nodePositions.push(v.x, v.y, v.z);
  }
  const nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute('position', new THREE.Float32BufferAttribute(nodePositions, 3));
  const nodes = new THREE.Points(
    nodeGeo,
    new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.22,
      sizeAttenuation: true,
      transparent: true,
      opacity: 1.0,
      map: dotTex,
      depthWrite: false,
    })
  );
  root.add(nodes);

  // Center sphere
  const coreMat = new THREE.MeshBasicMaterial({
    color: 0xea580c,
    transparent: true,
    opacity: 0.9,
  });
  const core = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 16), coreMat);
  root.add(core);

  // Ambient depth particles
  const PARTICLE_COUNT = 500;
  const pPositions = new Float32Array(PARTICLE_COUNT * 3);
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const r = 2.4 + Math.random() * 1.0;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    pPositions[i * 3 + 0] = r * Math.sin(phi) * Math.cos(theta);
    pPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    pPositions[i * 3 + 2] = r * Math.cos(phi);
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));
  const particles = new THREE.Points(
    pGeo,
    new THREE.PointsMaterial({
      color: 0xf59e0b,
      size: 0.055,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.75,
      map: dotTex,
      depthWrite: false,
    })
  );
  root.add(particles);

  // ═══════════════════════════════════════════════════════════
  //  Interaction & Resize Listeners
  // ═══════════════════════════════════════════════════════════
  const mouse = { x: 0, y: 0 };
  const tilt  = { x: 0, y: 0 };

  function onPointerMove(clientX, clientY) {
    mouse.x = (clientX / window.innerWidth) * 2 - 1;
    mouse.y = (clientY / window.innerHeight) * 2 - 1;
  }

  window.addEventListener('pointermove', (e) => onPointerMove(e.clientX, e.clientY), { passive: true });
  window.addEventListener('pointerleave', () => { mouse.x = 0; mouse.y = 0; });

  function resize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const aspect = w / h;

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h, false);

    camera.aspect = aspect;
    camera.position.z = aspect < 0.9 ? 7.4 : aspect < 1.3 ? 6.6 : 6.0;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  // ═══════════════════════════════════════════════════════════
  //  Animation Loop
  // ═══════════════════════════════════════════════════════════
  const clock = new THREE.Clock();
  let entryT = 0;
  const ENTRY_DURATION = 1.6;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rotationSpeed = prefersReduced ? 0.0 : 1.0;
  let idlePhase = 0;

  function tick() {
    const dt = Math.min(0.05, clock.getDelta());
    const t = clock.getElapsedTime();

    if (entryT < 1) {
      entryT = Math.min(1, entryT + dt / ENTRY_DURATION);
      const ease = 1 - Math.pow(1 - entryT, 3);
      root.scale.setScalar(0.7 + 0.3 * ease);
    }

    const targetX = mouse.y * 0.55;
    const targetY = mouse.x * 0.85;
    tilt.x += (targetX - tilt.x) * 0.06;
    tilt.y += (targetY - tilt.y) * 0.06;

    idlePhase += dt * 0.35;
    const driftX = Math.sin(idlePhase) * 0.06;
    const driftY = Math.cos(idlePhase * 0.7) * 0.08;

    root.rotation.x = tilt.x + driftX;
    root.rotation.y = tilt.y + driftY;
    root.position.x = tilt.y * 0.22;
    root.position.y = -tilt.x * 0.18 + Math.sin(t * 0.9) * 0.07;

    outerWire.rotation.y += dt * 0.16 * rotationSpeed;
    outerWire.rotation.x += dt * 0.05 * rotationSpeed;

    innerWire.rotation.y -= dt * 0.26 * rotationSpeed;
    innerWire.rotation.z += dt * 0.10 * rotationSpeed;

    network.rotation.y += dt * 0.10 * rotationSpeed;
    network.rotation.z -= dt * 0.045 * rotationSpeed;

    particles.rotation.y += dt * 0.045 * rotationSpeed;
    particles.rotation.x += dt * 0.02 * rotationSpeed;

    const pulse = 0.9 + Math.sin(t * 2.4) * 0.35;
    core.scale.setScalar(pulse);
    coreMat.opacity = 0.55 + Math.sin(t * 2.4) * 0.35;

    lightY.position.x = Math.cos(t * 0.4) * 3.2;
    lightY.position.z = Math.sin(t * 0.4) * 3.2 + 2;
    lightO.position.x = Math.cos(t * 0.3 + 2.0) * 3.5;
    lightO.position.z = Math.sin(t * 0.3 + 2.0) * 3.0 + 2;

    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  window.addEventListener('pagehide', () => {
    renderer.dispose();
  });
})();