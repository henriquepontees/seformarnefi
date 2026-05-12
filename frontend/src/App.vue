<script setup>
import { ref, onMounted } from "vue";

const API = "http://localhost:18000";

const token = ref(localStorage.getItem("tcc_token"));
const user = ref(null);
const erro = ref(null);

onMounted(async () => {
  // Após o redirect do callback, o JWT vem no fragment da URL.
  // Fragment é local ao navegador — não vai para logs HTTP do servidor.
  if (window.location.hash.startsWith("#token=")) {
    const t = window.location.hash.replace("#token=", "");
    localStorage.setItem("tcc_token", t);
    token.value = t;
    // Limpa o hash para não vazar o token na barra de endereços
    window.history.replaceState({}, "", window.location.pathname);
  }
  if (token.value) await buscarUsuario();
});

async function buscarUsuario() {
  // Bate no endpoint protegido /api/me com o JWT no header Authorization
  const res = await fetch(`${API}/api/me`, {
    headers: { Authorization: `Bearer ${token.value}` },
  });
  if (res.ok) {
    user.value = await res.json();
  } else {
    erro.value = "Sessão inválida ou expirada.";
    encerrarSessaoLocal();
  }
}

function entrar() {
  // Redireciona ao backend, que por sua vez redireciona ao Keycloak
  window.location.href = `${API}/api/auth/login`;
}

async function sair() {
  // Revoga o JWT no backend e descarta localmente
  if (token.value) {
    await fetch(`${API}/api/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token.value}` },
    });
  }
  encerrarSessaoLocal();
}

function encerrarSessaoLocal() {
  localStorage.removeItem("tcc_token");
  token.value = null;
  user.value = null;
}
</script>

<template>
  <main class="container">
    <h1>TCC SSO</h1>

    <div v-if="!user">
      <p>Você não está autenticado.</p>
      <button @click="entrar">Entrar com SSO</button>
      <p v-if="erro" class="erro">{{ erro }}</p>
    </div>

    <div v-else class="perfil">
      <h2>Olá, {{ user.nome || user.email }}</h2>
      <ul>
        <li><strong>sub:</strong> {{ user.sub }}</li>
        <li><strong>email:</strong> {{ user.email }}</li>
      </ul>
      <button @click="sair">Sair</button>
    </div>
  </main>
</template>

<style>
.container {
  font-family: system-ui, sans-serif;
  max-width: 480px;
  margin: 4rem auto;
  padding: 2rem;
}
button {
  padding: 0.6rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
}
.erro {
  color: #c0392b;
}
.perfil ul {
  list-style: none;
  padding: 0;
}
.perfil li {
  margin: 0.3rem 0;
}
</style>
