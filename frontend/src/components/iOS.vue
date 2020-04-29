<template>
  <Row>
    <i-col span="6" class="ios-split">
      <device-list class="device-list"/>
      <screen-shot v-show="focusDeviceId"/>
    </i-col>
    <i-col span="18" class="ios-split">
      <div style="height:100vh">
        <Split v-model="split" mode="vertical">
          <Row slot="top" class="ios-split-pane" style="height:100%">
            <device-info/>
          </Row>
          <Row slot="bottom" class="ios-split-pane" style="height:100%">
            <package-info/>
          </Row>
        </Split>
      </div>
    </i-col>
  </Row>
</template>

<script>
import DeviceList from '@/components/DeviceList.vue'
import DeviceInfo from '@/components/DeviceInfo.vue'
import ScreenShot from '@/components/ScreenShot.vue'
import PackageInfo from '@/components/PackageInfo.vue'
import { checkEnv } from '@/api'

export default {
  components: {
    DeviceList,
    DeviceInfo,
    ScreenShot,
    PackageInfo
  },
  data () {
    return {
      split: 0.5
    }
  },
  created () {
    this.checkEnvironment()
    this.$bus.$on('msg.success', this.successMessage)
    this.$bus.$on('msg.info', this.infoMessage)
    this.$bus.$on('msg.error', this.errorMessage)
  },
  computed: {
    focusDeviceId () {
      return this.$store.state.focusDeviceId
    }
  },
  methods: {
    checkEnvironment () {
      checkEnv()
        .then(
          this.$store.dispatch('loadDevices'),
          this.$io.on('ios-device', this.getDevices)
        )
        .catch(error => {
          this.$bus.$emit('msg.error', error.data.message)
        })
    },
    getDevices () {
      this.$store.dispatch('loadDevices')
    },
    successMessage (msg) {
      this.$Message.success({
        content: msg,
        duration: 3,
        closable: true
      })
    },
    infoMessage (msg) {
      this.$Message.info({
        content: msg,
        duration: 3,
        closable: true
      })
    },
    errorMessage (msg) {
      this.$Message.error({
        content: msg,
        duration: 0,
        closable: true
      })
    }
  }
}
</script>

<style>
.ios-split {
  height: 100vh;
  border-left:1px solid #e8eaec;
  border-right:1px solid #e8eaec;
  word-break: break-all;
}
.ios-split-pane{
  overflow-y: auto;
  height: 100%;
}
.cell-empty{
  position: absolute;
  top:40%;
  left:50%;
  transform:translate(-50%,-50%);
  text-align: center;
}
.device-list {
  height: 30vh;
}
.ios-img {
  height: calc(70vh - 10px);
}
.info-header {
  background-color: #f8f8f9;
  padding: 5px;
}
.ivu-tabs > .ivu-tabs-bar {
  border-bottom: 0px;
  background-color: #f8f8f9;
  margin-bottom: 0px;
  font-weight: bolder;
}
.ivu-tabs > .ivu-tabs-content {
  height: 100%;
}
</style>
