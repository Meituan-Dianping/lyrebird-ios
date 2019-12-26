<template>
  <div>
    <Row class="info-header" type="flex" align="middle">
      <i-col span="6">
        <strong>Device information</strong>
      </i-col>
      <i-col span="18" align="right">
        <Button type="primary" size="small" style="margin:0px 5px" @click.native="getDeviceDetail">more detail</Button>
      </i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>Device ID</b></i-col>
      <i-col span="16">{{deviceInfo.device_id}}</i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>Model</b></i-col>
      <i-col span="16">{{deviceInfo.model}}</i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>Device Name</b></i-col>
      <i-col span="16">{{deviceInfo.device_name}}</i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>OS Version</b></i-col>
      <i-col span="16">{{deviceInfo.os_version}}</i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>Phone Number</b></i-col>
      <i-col span="16">{{deviceInfo.phone_number}}</i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>Serial Number</b></i-col>
      <i-col span="16">{{deviceInfo.sn}}</i-col>
    </Row>
    <Modal v-model="showDeviceDetail" title="Detail" width="1000" :styles="{top: '5vh'}" :footer-hide=true>
      <pre style="height:70vh;overflow-x:auto;">{{deviceDetail}}</pre>
    </Modal>
  </div>
</template>

<script>
import * as api from '@/api'

export default {
  data () {
    return {
      showDeviceDetail: false,
      deviceDetail: null
    }
  },
  computed: {
    deviceInfo () {
      return this.$store.state.deviceInfo
    }
  },
  methods: {
    getDeviceDetail () {
      this.showDeviceDetail = true
      api.getDeviceDetail(this.deviceInfo.device_id)
        .then(response => {
          this.deviceDetail = response.data.device_detail
        })
    }
  }
}
</script>
