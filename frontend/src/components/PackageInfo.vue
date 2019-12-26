<template>
  <div>
    <Row class="info-header" type="flex" align="middle">
      <i-col span="8">
        <strong>App information</strong>
      </i-col>
      <i-col span="16" align="right">
        <Button type="primary" size="small" style="margin:0px 5px" @click.native="startApp" :disabled="isStartingApp || !packageName">Start App</Button>
        <Button type="primary" size="small" style="margin:0px 5px" @click.native="stopApp" :disabled="!packageName">Stop App</button>
      </i-col>
    </Row>
    <Row style="padding:10px;">
      <i-col span="8"><b>Application</b></i-col>
      <i-col span="16">
        <i-select size="small" v-model="packageName" placeholder="Application" filterable>
          <i-option v-for="item in packages" :value="item.bundle_id" :label="item.bundle_id" :key="item.bundle_id">
            <span>{{item.bundle_id}}</span>
            <span style="float:right;color:#ccc">{{item.app_name}}</span>
          </i-option>
        </i-select>
      </i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>App Name</b></i-col>
      <i-col span="16">
        <span>{{packageInfo.AppName}}</span>
      </i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>AppVersion</b></i-col>
      <i-col span="16">
        <span>{{packageInfo.VersionNumber}}</span>
      </i-col>
    </Row>
    <Row style="padding:10px">
      <i-col span="8"><b>Build Number</b></i-col>
      <i-col span="16">
        <span>{{packageInfo.BuildNumber}}</span>
      </i-col>
    </Row>
    <Spin fix v-if="isLoadingPackageInfo">
      <Icon type="ios-loading" size=18 class="spin-icon-load"></Icon>
      <div>Loading information of <b>{{packageName}}</b> </div>
    </Spin>
  </div>
</template>

<script>
export default {
  computed: {
    packageName: {
      get () {
        return this.$store.state.focusPackageName
      },
      set (val) {
        this.$store.commit('setFocusPackageName', val)
        this.$store.dispatch('loadPackageInfo')
      }
    },
    packages () {
      return this.$store.state.packages
    },
    packageInfo () {
      return this.$store.state.packageInfo
    },
    isLoadingPackageInfo () {
      return this.$store.state.isLoadingPackageInfo
    },
    isStartingApp () {
      return this.$store.state.isStartingApp
    }
  },
  methods: {
    startApp () {
      this.$store.dispatch('startApp')
    },
    stopApp () {
      this.$store.dispatch('stopApp')
    }
  }
}
</script>

<style>
  .spin-icon-load{
    animation: ani-demo-spin 1s linear infinite;
  }
</style>
