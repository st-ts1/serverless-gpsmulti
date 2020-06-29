// CDNのElementで日本語を使う
ELEMENT.locale(ELEMENT.lang.ja)

new Vue({
    el: '#app',

    data: {
        map: null, // Leafletのmap
        gpsdata: [], // DyanmoDBのデータ
        loginVisible: true,  // ログインプロンプトを表示するか?
        api: "", // API Gatewayのホスト部
        user: "",
        imsi: "",
        loginpasswd: "",
        // 取得数select用
        selectoptions: [{
            value: '1',
            label: '取得数1'
        }, {
            value: '10',
            label: '取得数10'
        }, {
            value: '100',
            label: '取得数100'
        }
        ],
        selectedvalue: '1',
        // 日時指定。ここより古い値を取得する
        datetimevalue: 0
    },

    methods: {
        handleClose: function () {
            // ログインプロンプトをclose
            console.log("handleClose")
            this.loginVisible = false
        },
        draw_all: function () {
            // DynamoDBからデータ取得し描画する
            let vm = this;

            if (vm.loginVisible == true) {
                // ログイン前は何もしない
                return;
            }

            // 呼び出しURL作成
            let apistr = "https://"+vm.api+".execute-api.us-west-2.amazonaws.com/v1/gps-data?imsi="+vm.imsi+"&sort=desc";
            apistr = apistr + "&limit=" + vm.selectedvalue
            if (vm.datetimevalue != 0) {
                // 日時指定が有るため、GETオプション追加
                apistr = apistr + "&to=" + vm.datetimevalue
            }
            vm.lodash_debounce_axios(apistr);

        },
        // lodash _のdebounceで呼び出しを遅延している。連続して呼ばないように
        lodash_debounce_axios: _.debounce(function(apistr) {
            let vm = this;
            axios
            .get(apistr, {
                headers: { Authorization: vm.loginpasswd },
                params: {}
            })
            // thenで成功した場合の処理をかける
            .then(response => {
                console.log("status:", response.status); // 200
                console.log(response.data); // response body.
                if (response.status != 200) {
                    console.log("読み込み失敗");
                    vm.$message.error('読み込みエラー ' + response.status);
                    vm.loginVisible = true;
                } else {
                    //vm.message = response.data;
                    console.log("読み込み成功");
                    //json_data = JSON.parse(response.data)
                    //vm.todos = response.data.todos;
                    // 全てのデータを一時削除(連続して呼ばれた時に困るので書き換え直前に消す)
                    vm.remove_all();
                    let firstdata = true;
                    for (i of response.data.Items) {
                        // 1データ毎に処理
                        let tmp_date = new Date(i.timestamp);
                        let lll = null;
                        if (i.payloads.lat != null) {
                            // LeafLetにマーカー追加
                            lll = L.marker([i.payloads.lat, i.payloads.lon], { title: tmp_date.toString() })
                            lll.addTo(vm.map);
                        }
                        // Vue.jsにデータ追加
                        let tmp_dict = {
                            lat: i.payloads.lat,
                            lon: i.payloads.lon,
                            time: tmp_date.toString(),
                            bat: i.payloads.bat,
                            temp: i.payloads.temp,
                            humi: i.payloads.humi,
                            type: i.payloads.type,
                            layer: lll
                        }
                        vm.gpsdata.push(tmp_dict);

                        if (firstdata == true) {
                            // 初めのデータが画面中央となるようにする
                            //vm.map.panTo([i.payloads.lat, i.payloads.lon]);
                            //vm.map.setZoom(10);
                            vm.map.setView([i.payloads.lat, i.payloads.lon], 15,
                                {
                                    "animate": true,
                                    "pan": { "duration": 10 }
                                });
                            firstdata = false;
                        }
                    }
                    //console.log(vm.todos.length);
                    vm.$message("読み込み成功");
                }
            })
            // catchでエラー時の挙動を定義する
            .catch(err => {
                console.log("axios err:", err);
                console.log("ロード時に予期せぬエラー");
                vm.$message.error('ロード時に予期せぬエラー');
                vm.loginVisible = true;
            });

        }, 1000),
        remove_all: function () {
            // 描画とGPSデータをすべて消す
            let vm = this;
            let tmp;
            while ((tmp = vm.gpsdata.pop()) != undefined) {
                // 緯度経度情報なしの場合nullとなっている
                if (tmp.layer != null) {
                    // 地図からレイヤー削除
                    tmp.layer.remove();
                    console.log("remove:" + tmp.time)
                }
            }
        }
    },

    watch: {
        selectedvalue: {
            handler: function (newvalue) {
                let vm = this;
                console.log(newvalue);
                vm.draw_all();
            }
        },
        datetimevalue: {
            handler: function (newvalue) {
                console.log(newvalue);
                let vm = this;
                console.log(newvalue);
                vm.draw_all();
            }
        },
        loginVisible: {
            // 引数はウォッチしているプロパティの変更後の値
            handler: function (loginVisible) {
                var vm = this;
                if (loginVisible == true) {
                    // login画面を表示されるように変更された
                    return;
                }
                //console.log(vm.loginpasswd);
                vm.draw_all();

            },
            // deep オプションでネストしているデータも監視できる
            deep: true
        }
    },
    mounted: function () {
        var vm = this;
        console.log('mounted')
        console.log(this.$el)
        //地図を表示するdiv要素のidを設定
        vm.map = L.map('mapcontainer');
        //地図の中心とズームレベルを指定
        vm.map.setView([35.40, 136], 5);
        //表示するタイルレイヤのURLとAttributionコントロールの記述を設定して、地図に追加する
        L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
            attribution: "<a href='https://maps.gsi.go.jp/development/ichiran.html' target='_blank'>地理院タイル</a>"
        }).addTo(vm.map);
        // 現在時刻を設定
        let date = new Date();
        vm.datetimevalue = date.getTime();
    }
});