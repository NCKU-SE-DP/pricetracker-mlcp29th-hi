<template>
  <NavBar class="navbar"></NavBar>
  <RouterView class="render"></RouterView>
</template>

<script>
// import { RouterView } from 'vue-router';
import NavBar from './components/NavBar.vue'
export default {
  name: 'App',
  components: {
    NavBar,
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  overflow-x: auto;
}
.navbar{
  z-index: 1000;
  position: fixed;
  top: 0;
}
.render{
  margin-top: 4.5em;
  min-width: 320px;
  width: 100%;
  padding: 3em min(5em, max(1.5em, 10%));
  background: #f3f3f3;
  min-height: calc(100vh - 4.5em);
  height: calc(100% - 4.5em);
  box-sizing: border-box;
}
</style>