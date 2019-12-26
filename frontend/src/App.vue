<template>
  <div id="app">
    <iOS/>
  </div>
</template>

<script>
import iOS from './components/iOS.vue'

export default {
  name: 'app',
  components: {
    iOS
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
</style>
