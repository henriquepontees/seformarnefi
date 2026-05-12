<script setup>
import { ref, onMounted } from "vue";

const status = ref("carregando...");

onMounted(async () => {
  // Verifica se o backend está respondendo. /api/health é público.
  const res = await fetch("http://localhost:18000/api/health");
  const data = await res.json();
  status.value = data.status;
});
</script>

<template>
  <main>
    <h1>TCC SSO — Frontend</h1>
    <p>Backend: {{ status }}</p>
  </main>
</template>
