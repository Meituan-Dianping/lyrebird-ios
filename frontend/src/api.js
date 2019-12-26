import axios from 'axios'
const API_PREFIX = '/plugins/ios/api'

const successHandler = (response) => {
  if (!response.data.hasOwnProperty('code')) {
    return Promise.reject(response)
  } else if (response.data.code !== 1000) {
    return Promise.reject(response)
  } else {
    return response
  }
}

const errorHandler = (error) => {
  return Promise.reject(error)
}

axios.interceptors.response.use(successHandler, errorHandler)

export const getDevices = () => {
  return axios({
    url: API_PREFIX + '/devices'
  })
}

export const getAppInfo = (deviceId, packageName) => {
  return axios({
    url: API_PREFIX + '/apps/' + deviceId + '/' + packageName
  })
}

export const getPackageName = () => {
  return axios({
    url: API_PREFIX + '/conf'
  })
}

export const getDeviceDetail = (deviceId) => {
  return axios({
    url: API_PREFIX + '/device/' + deviceId
  })
}

export const getPackages = (deviceId) => {
  return axios({
    url: API_PREFIX + '/apps/' + deviceId
  })
}

export const getScreenShot = (deviceId) => {
  return axios({
    url: API_PREFIX + '/screenshot/' + deviceId
  })
}

export const startApp = (deviceId, packageName) => {
  return axios({
    url: API_PREFIX + '/start_app/' + deviceId + '/' + packageName
  })
}

export const stopApp = (deviceId, packageName) => {
  return axios({
    url: API_PREFIX + '/stop_app/' + deviceId + '/' + packageName
  })
}
