Search.setIndex({docnames:["about","api_docs/modules","api_docs/pydra","api_docs/pydra.core","api_docs/pydra.core.messaging","api_docs/pydra.core.saving","api_docs/pydra.gui","api_docs/pydra.gui.toolbar","api_docs/pydra.modules","api_docs/pydra.modules.cameras","api_docs/pydra.modules.cameras.workers","api_docs/pydra.modules.optogenetics","api_docs/pydra.modules.tracking","api_docs/pydra.modules.tracking.tail_tracker","api_docs/pydra.utilities","api_guide","getting_started/installation","getting_started/using_pydra","index","new_structure/0_overview","structure/0_overview","structure/1_messaging","structure/2_network","structure/3_objects","structure/4_gui","structure/5_qt","structure/6_modules","structure/7_pipelines","tutorial/0_hello_world","tutorial/1_communication_between_workers","tutorial/2_events_with_arguments","tutorial/3_passing_data_between_workers","tutorial/4_data_types","tutorial/5_pydra_gui","tutorial/6_advanced_functionality","tutorial_welcome"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":5,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.viewcode":1,sphinx:56},filenames:["about.rst","api_docs\\modules.rst","api_docs\\pydra.rst","api_docs\\pydra.core.rst","api_docs\\pydra.core.messaging.rst","api_docs\\pydra.core.saving.rst","api_docs\\pydra.gui.rst","api_docs\\pydra.gui.toolbar.rst","api_docs\\pydra.modules.rst","api_docs\\pydra.modules.cameras.rst","api_docs\\pydra.modules.cameras.workers.rst","api_docs\\pydra.modules.optogenetics.rst","api_docs\\pydra.modules.tracking.rst","api_docs\\pydra.modules.tracking.tail_tracker.rst","api_docs\\pydra.utilities.rst","api_guide.rst","getting_started\\installation.rst","getting_started\\using_pydra.rst","index.rst","new_structure\\0_overview.rst","structure\\0_overview.rst","structure\\1_messaging.rst","structure\\2_network.rst","structure\\3_objects.rst","structure\\4_gui.rst","structure\\5_qt.rst","structure\\6_modules.rst","structure\\7_pipelines.rst","tutorial\\0_hello_world.rst","tutorial\\1_communication_between_workers.rst","tutorial\\2_events_with_arguments.rst","tutorial\\3_passing_data_between_workers.rst","tutorial\\4_data_types.rst","tutorial\\5_pydra_gui.rst","tutorial\\6_advanced_functionality.rst","tutorial_welcome.rst"],objects:{"":[[2,0,0,"-","pydra"]],"pydra.configuration":[[2,1,1,"","BackendConfig"],[2,1,1,"","Configuration"],[2,1,1,"","Port"],[2,1,1,"","PortManager"],[2,1,1,"","PublisherConfig"],[2,1,1,"","PydraConfig"],[2,1,1,"","ReceiverConfig"],[2,1,1,"","SaverConfig"],[2,1,1,"","SenderConfig"],[2,1,1,"","SubscriberConfig"],[2,1,1,"","WorkerConfig"]],"pydra.configuration.BackendConfig":[[2,2,1,"","subscriptions"]],"pydra.configuration.Configuration":[[2,3,1,"","connections"],[2,2,1,"","name"]],"pydra.configuration.Port":[[2,3,1,"","read"],[2,3,1,"","val"],[2,3,1,"","write"]],"pydra.configuration.PortManager":[[2,4,1,"","next"]],"pydra.configuration.PublisherConfig":[[2,2,1,"","publisher"],[2,2,1,"","sub"]],"pydra.configuration.PydraConfig":[[2,2,1,"","subscriptions"]],"pydra.configuration.ReceiverConfig":[[2,4,1,"","add_receiver"],[2,2,1,"","receivers"]],"pydra.configuration.SaverConfig":[[2,2,1,"","subscriptions"]],"pydra.configuration.SenderConfig":[[2,2,1,"","recv"],[2,2,1,"","sender"]],"pydra.configuration.SubscriberConfig":[[2,4,1,"","add_subscription"],[2,2,1,"","subscriptions"]],"pydra.configuration.WorkerConfig":[[2,2,1,"","subscriptions"]],"pydra.core":[[4,0,0,"-","messaging"],[3,0,0,"-","protocol"],[3,0,0,"-","trigger"]],"pydra.core.messaging":[[4,2,1,"","DATA"],[4,1,1,"","PydraMessage"],[4,0,0,"-","serializers"]],"pydra.core.messaging.PydraMessage":[[4,4,1,"","callback"],[4,4,1,"","decode"],[4,2,1,"","decoders"],[4,2,1,"","dtypes"],[4,4,1,"","encode"],[4,2,1,"","encoders"],[4,2,1,"id0","flag"],[4,4,1,"","message_tags"],[4,4,1,"","reader"],[4,4,1,"","recv"],[4,4,1,"","serializer"]],"pydra.core.messaging.serializers":[[4,5,1,"","deserialize_array"],[4,5,1,"","deserialize_bool"],[4,5,1,"","deserialize_dict"],[4,5,1,"","deserialize_float"],[4,5,1,"","deserialize_int"],[4,5,1,"","deserialize_object"],[4,5,1,"","deserialize_string"],[4,5,1,"","serialize_array"],[4,5,1,"","serialize_bool"],[4,5,1,"","serialize_dict"],[4,5,1,"","serialize_float"],[4,5,1,"","serialize_int"],[4,5,1,"","serialize_objet"],[4,5,1,"","serialize_string"]],"pydra.core.protocol":[[3,1,1,"","Protocol"],[3,1,1,"","Queued"],[3,1,1,"","Timer"],[3,1,1,"","TriggerContainer"]],"pydra.core.protocol.Protocol":[[3,4,1,"","addEvent"],[3,4,1,"","addTimer"],[3,4,1,"","addTrigger"],[3,4,1,"","build"],[3,4,1,"","clearFlag"],[3,2,1,"","completed"],[3,4,1,"","end"],[3,2,1,"","event_queue"],[3,2,1,"","finished"],[3,2,1,"","flag"],[3,4,1,"","freeRunningMode"],[3,4,1,"","interrupt"],[3,2,1,"","interrupted"],[3,2,1,"","rep"],[3,4,1,"","running"],[3,4,1,"","setFlag"],[3,4,1,"","setInterval"],[3,4,1,"","setRepetitions"],[3,4,1,"","start"],[3,2,1,"","started"],[3,2,1,"","timer"]],"pydra.core.protocol.Queued":[[3,2,1,"","finished"],[3,4,1,"","interrupt"]],"pydra.core.protocol.Timer":[[3,2,1,"","finished"],[3,4,1,"","interrupt"],[3,4,1,"","timeout"]],"pydra.core.protocol.TriggerContainer":[[3,2,1,"","finished"],[3,4,1,"","interrupt"],[3,2,1,"","interrupted"],[3,4,1,"","timed_out"],[3,2,1,"","timeout"],[3,4,1,"","trigger_received"]],"pydra.gui":[[6,0,0,"-","connections"],[6,0,0,"-","main"],[6,0,0,"-","module"],[6,0,0,"-","plotter"],[6,0,0,"-","protocol"],[6,0,0,"-","states"],[7,0,0,"-","toolbar"],[6,0,0,"-","widgets"]],"pydra.gui.connections":[[6,1,1,"","ConnectivityWidget"],[6,1,1,"","Editor"],[6,1,1,"","ItemAssignmentWidget"],[6,1,1,"","NetworkConfiguration"],[6,1,1,"","QButtonAdd"],[6,1,1,"","QComboBoxLinked"]],"pydra.gui.connections.Editor":[[6,4,1,"","newValue"],[6,2,1,"","new_value"]],"pydra.gui.connections.ItemAssignmentWidget":[[6,4,1,"","addItem"],[6,4,1,"","addRow"],[6,4,1,"","changeItem"],[6,4,1,"","columnCount"],[6,4,1,"","enterNew"],[6,4,1,"","getValue"],[6,4,1,"","indexChanged"],[6,4,1,"","rowCount"],[6,2,1,"","updateChildren"]],"pydra.gui.connections.NetworkConfiguration":[[6,3,1,"","connections"],[6,4,1,"","run"]],"pydra.gui.connections.QButtonAdd":[[6,4,1,"","buttonClicked"],[6,2,1,"","button_clicked"]],"pydra.gui.connections.QComboBoxLinked":[[6,4,1,"","checkIndex"],[6,2,1,"","current_index_changed"]],"pydra.gui.main":[[6,1,1,"","MainWindow"]],"pydra.gui.main.MainWindow":[[6,4,1,"","add_controller"],[6,4,1,"","add_plotter"],[6,4,1,"","closeEvent"],[6,4,1,"","enterRunning"],[6,4,1,"","run_protocol"],[6,4,1,"","update_plots"]],"pydra.gui.module":[[6,1,1,"","ControlWidget"],[6,1,1,"","PydraDockWidget"],[6,5,1,"","disabled"]],"pydra.gui.module.ControlWidget":[[6,4,1,"","receiveLogged"],[6,2,1,"","sendEvent"],[6,4,1,"","send_event"],[6,2,1,"","updatePlots"],[6,3,1,"","update_enabled"]],"pydra.gui.module.PydraDockWidget":[[6,4,1,"","closeEvent"],[6,4,1,"","send_event"],[6,4,1,"","toggle_visibility"]],"pydra.gui.plotter":[[6,1,1,"","DisplayContainer"],[6,1,1,"","Plotter"]],"pydra.gui.plotter.DisplayContainer":[[6,4,1,"","add"]],"pydra.gui.plotter.Plotter":[[6,4,1,"","addImagePlot"],[6,4,1,"","addParamPlot"],[6,4,1,"","clear_data"],[6,4,1,"","updateImage"],[6,4,1,"","updateOverlay"],[6,4,1,"","updateParam"],[6,4,1,"","updatePlots"]],"pydra.gui.protocol":[[6,1,1,"","EventWidget"],[6,1,1,"","ProtocolBuilder"],[6,1,1,"","ProtocolWindow"],[6,1,1,"","TimerWidget"]],"pydra.gui.protocol.EventWidget":[[6,4,1,"","selectionChanged"],[6,4,1,"","set"],[6,3,1,"","value"]],"pydra.gui.protocol.ProtocolBuilder":[[6,4,1,"","add_event"],[6,4,1,"","add_timer"],[6,4,1,"","clear"],[6,2,1,"","default_events"],[6,4,1,"","initUI"],[6,3,1,"","protocol"],[6,4,1,"","remove"],[6,4,1,"","separator"],[6,4,1,"","updateUI"]],"pydra.gui.protocol.ProtocolWindow":[[6,4,1,"","loadProtocol"],[6,3,1,"","name"],[6,4,1,"","newProtocol"],[6,3,1,"","protocol"],[6,4,1,"","saveProtocol"],[6,4,1,"","setProtocol"]],"pydra.gui.protocol.TimerWidget":[[6,4,1,"","set"],[6,3,1,"","value"]],"pydra.gui.states":[[6,1,1,"","StateEnabled"]],"pydra.gui.states.StateEnabled":[[6,4,1,"","endRecord"],[6,4,1,"","enterIdle"],[6,4,1,"","enterRunning"],[6,4,1,"","startRecord"]],"pydra.gui.toolbar":[[7,1,1,"","RecordButton"],[7,1,1,"","RecordingToolbar"],[7,5,1,"","checked"],[7,0,0,"-","directory_widget"],[7,0,0,"-","file_naming"],[7,0,0,"-","protocol_widget"]],"pydra.gui.toolbar.RecordButton":[[7,4,1,"","enterIdle"],[7,4,1,"","enterRunning"]],"pydra.gui.toolbar.RecordingToolbar":[[7,2,1,"","record"],[7,4,1,"","record_button_clicked"],[7,4,1,"","set_filename"],[7,4,1,"","set_working_directory"],[7,4,1,"","show_protocol"]],"pydra.gui.toolbar.directory_widget":[[7,1,1,"","DirectoryWidget"]],"pydra.gui.toolbar.directory_widget.DirectoryWidget":[[7,4,1,"","change_directory"],[7,2,1,"","changed"],[7,4,1,"","enterIdle"],[7,4,1,"","enterRunning"]],"pydra.gui.toolbar.file_naming":[[7,1,1,"","FileNamingWidget"]],"pydra.gui.toolbar.file_naming.FileNamingWidget":[[7,3,1,"","autonaming_enabled"],[7,4,1,"","change_basename"],[7,2,1,"","changed"],[7,3,1,"","editor_text"],[7,4,1,"","endRecord"],[7,4,1,"","enterIdle"],[7,4,1,"","enterRunning"],[7,3,1,"","filename"],[7,4,1,"","toggle_autonaming"],[7,4,1,"","update_filename"]],"pydra.gui.toolbar.protocol_widget":[[7,1,1,"","ProtocolWidget"]],"pydra.gui.toolbar.protocol_widget.ProtocolWidget":[[7,4,1,"","editProtocol"],[7,2,1,"","editor_clicked"],[7,4,1,"","endRecord"],[7,4,1,"","enterIdle"],[7,4,1,"","enterRunning"],[7,4,1,"","initUI"],[7,4,1,"","startRecord"],[7,4,1,"","update_protocol"],[7,3,1,"","value"]],"pydra.gui.widgets":[[6,1,1,"","DoubleSpinboxWidget"],[6,1,1,"","SpinboxWidget"]],"pydra.gui.widgets.DoubleSpinboxWidget":[[6,4,1,"","setValue"],[6,3,1,"","value"],[6,2,1,"","valueChanged"]],"pydra.gui.widgets.SpinboxWidget":[[6,4,1,"","setValue"],[6,3,1,"","value"],[6,2,1,"","valueChanged"]],"pydra.modules":[[9,0,0,"-","cameras"],[11,0,0,"-","optogenetics"],[12,0,0,"-","tracking"]],"pydra.modules.cameras":[[9,0,0,"-","widget"]],"pydra.modules.cameras.widget":[[9,1,1,"","CameraWidget"],[9,1,1,"","ExposureWidget"],[9,1,1,"","FramePlotter"],[9,1,1,"","FrameRateWidget"],[9,1,1,"","FrameSizeWidget"],[9,1,1,"","ParameterGroupBox"]],"pydra.modules.cameras.widget.CameraWidget":[[9,4,1,"","enterIdle"],[9,4,1,"","enterRunning"],[9,4,1,"","param_changed"],[9,4,1,"","receiveLogged"],[9,4,1,"","set_params"]],"pydra.modules.cameras.widget.ExposureWidget":[[9,3,1,"","param_dict"]],"pydra.modules.cameras.widget.FramePlotter":[[9,4,1,"","updatePlots"]],"pydra.modules.cameras.widget.FrameRateWidget":[[9,3,1,"","param_dict"]],"pydra.modules.cameras.widget.FrameSizeWidget":[[9,3,1,"","param_dict"]],"pydra.modules.cameras.widget.ParameterGroupBox":[[9,4,1,"","addDoubleSpinBox"],[9,4,1,"","addSpinBox"],[9,4,1,"","confirm_changes"],[9,2,1,"","param_changed"],[9,3,1,"","param_dict"],[9,4,1,"","set_values"],[9,3,1,"","values"]],"pydra.modules.optogenetics":[[11,0,0,"-","widget"],[11,0,0,"-","worker"]],"pydra.modules.optogenetics.widget":[[11,1,1,"","OptogeneticsWidget"]],"pydra.modules.optogenetics.widget.OptogeneticsWidget":[[11,4,1,"","connect_to_laser"],[11,4,1,"","disconnect_from_laser"],[11,4,1,"","enterIdle"],[11,4,1,"","enterRunning"],[11,2,1,"","plot"],[11,4,1,"","toggle_laser"],[11,4,1,"","updatePlots"]],"pydra.modules.optogenetics.worker":[[11,1,1,"","OptogeneticsWorker"]],"pydra.modules.optogenetics.worker.OptogeneticsWorker":[[11,4,1,"","cleanup"],[11,2,1,"","name"],[11,4,1,"","stimulation_off"],[11,4,1,"","stimulation_on"]],"pydra.modules.tracking":[[13,0,0,"-","tail_tracker"]],"pydra.pydra":[[2,1,1,"","Pydra"]],"pydra.pydra.Pydra":[[2,4,1,"","configure"],[2,2,1,"","name"],[2,4,1,"","run"]],"pydra.utilities":[[14,0,0,"-","clock"],[14,0,0,"-","labjack"]],"pydra.utilities.clock":[[14,1,1,"","ClockMeta"],[14,1,1,"","clock"]],"pydra.utilities.clock.ClockMeta":[[14,4,1,"","reset"],[14,3,1,"","t"],[14,3,1,"","t0"]],"pydra.utilities.labjack":[[14,1,1,"","LabJack"]],"pydra.utilities.labjack.LabJack":[[14,4,1,"","connect"],[14,2,1,"","registers"],[14,4,1,"","send_signal"]],pydra:[[2,0,0,"-","configuration"],[3,0,0,"-","core"],[6,0,0,"-","gui"],[8,0,0,"-","modules"],[2,0,0,"-","pydra"],[14,0,0,"-","utilities"]]},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","property","Python property"],"4":["py","method","Python method"],"5":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:property","4":"py:method","5":"py:function"},terms:{"0":[9,28,29,30,31,32,34],"01":34,"0mq":[28,29,30,31,33],"1":[28,29,30,31,32,34],"10":[30,31],"125":34,"2":[6,23],"200":32,"250":34,"255":34,"3":23,"300":32,"50":34,"5000":14,"5002":14,"byte":4,"case":[3,23],"class":[2,3,4,6,7,9,11,14,17,19,21,22,23,28,29,30,31,32,33,34],"default":[9,23],"do":[16,17,19,22,23,33],"final":[19,21,23],"float":[3,4,19,21],"function":[3,4,18,19,21,23,33],"import":[18,28,29,30,31,32,33,34],"int":[3,4,6,7,19,21],"new":[12,22,23,28],"public":2,"return":[3,4,17,22,23],"static":[2,4,6,16],"super":[17,23,28,29,30,31,32,33,34],"true":[6,34],"void":22,"while":[19,21,23],A:[2,3,4,17,18,22],As:[19,22,33],At:[19,21,31,33],BE:12,FOR:12,For:[0,3,16,17,18,19,21,23],If:[16,22,23],In:[19,21,22,23,28],It:[0,16,18,19,21,34],No:3,OF:12,OR:17,THE:28,TO:12,The:[3,4,6,16,19,21,22,23,28,32,33,35],There:[19,21],These:[3,19,21,22,23],To:[16,17,19,28,33,35],__call__:3,__init__:[17,28,29,30,31,32,33,34],__main__:[17,28,29,30,31,32,33,34],__name__:[17,28,29,30,31,32,33,34],_connect:19,_data:19,_error:19,_process:23,_static:22,a_byt:4,abl:[4,16],about:[0,18,19,23,35],abov:[19,23],access:[22,33],account:16,achiev:[19,22],acquaint:19,acquir:[31,34],acquisit:[31,34],acquisitionwidget:34,acquisitionwork:34,across:14,activ:[16,35],ad:[18,23,28],add:[3,6,17,18,28,29,30,31,32,33,34],add_control:6,add_ev:6,add_plott:6,add_receiv:2,add_subscript:2,add_tim:6,adddoublespinbox:9,addev:3,addimageplot:6,addit:[4,18,19,21,22,23],additem:6,addition:28,addparamplot:6,addrow:[6,34],addspinbox:9,addtim:3,addtrigg:3,addwidget:33,advanc:[18,23],advantag:[19,21],affect:23,after:[3,22,23,28],again:34,alia:4,all:[0,3,18,19,21,22,23,28],allow:[0,3,16,18,19,21,23,28,29,31],along:[4,23],also:[0,3,16,18,19,21,23,35],alter:[19,21],altern:35,although:[0,18],alwai:[0,17,18,23,33,34],among:23,an:[3,16,17,19,22,23,28,29,30,33,34],anaconda:16,ani:[0,3,17,18,19,21,22,23,33],anoth:[19,21],answer:16,anyth:17,appear:23,append:17,applic:[6,28],appropri:22,ar:[3,4,16,17,19,21,22,23,28,31,32,34,35],architectur:[19,21,23],arg:[3,4,6,7,9,11,14,17,28,29,30,31,32,33,34],argument:[3,18,23,28],around:35,arrai:[19,21,23,34],arriv:23,assign:[23,28],associ:[17,19,21,23],astyp:34,attribut:[2,4,17,23,30,32,33,34],automat:[17,19,21,23],autonaming_en:7,avail:[19,21],awar:19,b:[4,19],b_byte:4,back:[16,19],backchannel:19,backend:[2,19],backendconfig:2,bar:29,bare:23,base:[1,2,4,6,7,9,11,14,16,19,21,23],basic:[17,19,21],becaus:23,becom:22,been:[22,23,28],befor:[3,4,11,16],begin:17,behavior:[19,21],being:22,below:[17,19,21],between:[3,4,18,21,22,23,28],beyond:33,bi:[0,18],bind:[19,21],block:23,bool:[3,4],broadcast:[17,22,23,28,31,34],build:[0,3,18],built:[0,18],button:[6,33,34],button_click:[6,33],buttonclick:6,c:16,call:[3,4,11,17,19,21,23,28,29,30,31,32,33,34],callabl:3,callback:4,camera:[2,8,34],camerawidget:9,can:[3,16,17,19,21,22,23,28,33,34,35],cannot:[16,33],caus:[3,22],caveat:23,cd:16,chang:[7,23,30,34],change_basenam:7,change_directori:7,changeitem:6,channel:[19,22],charact:4,check:[7,16,22,23,28],checkindex:6,choic:16,choos:22,classmethod:3,clean:28,cleanup:[11,23],clear:[3,6],clear_data:6,clearflag:3,click:[16,33,34],clock:[1,2],clockmeta:14,clone:18,close:[17,28,33],closeev:6,code:[0,12,15,16,17,18,19,23,33,35],cog:16,col:9,columncount:6,combin:[19,21],come:[19,21],command:[16,35],common:23,commun:[0,16,17,18,21,22,23],complet:[3,16],complex:[19,21],complic:22,compon:[14,15],comprehens:[19,21],comput:[16,19,21,23],conda:16,config:[2,17,28,29,30,31,32,33,34],configur:[1,17,18,19,21,28,29,30,31,32,33,34],confirm_chang:9,conflict:19,connect:[1,2,3,14,17,19,21,22,23,28,29,30,31,33,34],connect_to_las:11,connectivitywidget:6,consid:23,consist:23,constantli:23,constructor:[4,17,23,28,34],contact:[0,18],contain:[3,4,16,22,23],content:1,continu:[3,22],control:[3,33,34],controlwidget:[6,9,11,33,34],conveni:23,coordin:[19,21,34],copi:[16,35],core:[1,2,11,15,17,19,28,29,30,31,32,33,34],correct:[19,21],correctli:[16,17],correspond:[23,28,29,30,31,33],counter:31,crash:22,creat:[2,3,16,18,19,21,23,28,29,30,31,32,33,34],current:[3,31,32],current_index_chang:6,curv:16,custom:[19,21,23],d:[4,34],d_byte:4,dac0:14,dac1:14,data:[4,6,17,18,19,21,22,23,33,34],data_cach:[6,9,11,34],data_typ:32,datamessag:4,datareceiv:32,datasend:32,dct:14,de:[0,18],debug:17,dec:6,decod:[4,19,21],decor:[19,21,23],deeper:19,def:[17,28,29,30,31,32,33,34],default_ev:6,defin:[15,17,19],deliv:[0,18,23],depend:21,descript:[19,21],deseri:[4,19,21],deserialize_arrai:4,deserialize_bool:4,deserialize_dict:4,deserialize_float:4,deserialize_int:4,deserialize_object:4,deserialize_str:4,design:[0,18,35],desir:19,destin:23,detail:23,dict:[2,3,4,6,19,21,32,34],dictionari:[2,21,23,28],differ:[21,23,32],direct:22,directli:[16,17],directori:[6,7,16,23,35],directory_widget:[2,6],directorywidget:7,disabl:[6,34],disconnect_from_las:11,displai:[1,2],displaycontain:6,distribut:23,dockwidget:33,doe:[16,23],done:28,doublespinboxwidget:6,download:16,downsid:[19,21],dropdown:16,dtype:4,duncan:[0,18],durat:3,e:[16,19,21],each:[0,3,4,18,19,21,22,23,34],edit:16,editor:6,editor_click:7,editor_text:7,editprotocol:7,effect:22,egg:[29,31,32],eggs_ev:29,eggswork:[29,31],either:22,elaps:3,elif:32,els:32,emit:[3,6],enabl:34,encod:[4,19,21],end:[3,19,21,22,31],endless:22,endrecord:[6,7],ensur:[23,28],enter:[3,23,34],enteridl:[6,7,9,11,34],enternew:6,enterrun:[6,7,9,11,34],env:16,environ:[18,35],error:19,especi:[19,21],essenc:22,establish:23,even:[22,23],event:[3,6,17,18,19,21,22,23,28,29,31,32,33,34],event_nam:[6,9],event_queu:3,eventwidget:6,everi:[23,28,29,30,31,34],everyth:[19,21],ex:16,exact:23,exampl:28,exclus:22,exist:[16,19,23],exit:[17,19,21,22,23,28,29,30,31,32,33],experiment:[0,18],exposurewidget:9,extend:19,extens:[19,21,35],extern:3,f:[4,16,19,21,29,30,31,32,33,34],f_byte:4,factori:2,fals:[3,34],few:23,file:[16,23],file_nam:[2,6],filenam:7,filenamingwidget:7,find:16,finicki:[19,21],finish:[3,28,34],first:[16,19,21,23,28],flag:[3,4,19,21],flexibl:[0,18,19,22],folder:16,foo:29,foremost:[19,21],fork:18,form:22,format:[19,21],forward:[22,23],found:[16,19,21],four:19,frame:[17,19,21,23,32,34],frameplott:[9,34],frameratewidget:9,framesizewidget:9,framework:19,frandom:34,free:[3,16,23],freerun:3,freerunningmod:3,from:[3,4,6,16,17,19,22,23,28,29,30,31,32,33,34,35],front:[0,18],frontend:[2,4,19],furthermor:23,futur:16,g:[19,21],gain:19,gap:3,gener:[2,4,19,21,34],get:[22,31,32,34],getvalu:6,github:18,give:17,given:17,go:16,goodbye_world:28,graphic:[0,18],graphicslayoutwidget:6,great:35,group:6,gui:[0,1,2,9,11,14,15,18,34],guid:[19,21],gut:[19,21],ha:[0,16,18,19,21,22,23,28,32,33,34],handl:[19,21,23],handler:[19,21,22,23,28],happen:[22,35],have:[16,19,21,22,23,28,29,30,31,34],heart:21,hello:[18,32,33],hello_world:[28,33],hellowidget:33,helloworld:[28,33],help:[16,19,21,33],helper:15,here:[16,17,19,21],higher:16,highlight:23,hood:[19,21,28],how:[17,19,35],howev:[19,21,22,23],hydra:[0,18],i:[4,6,7,16,17,19,21,30,32,34],i_byt:4,id:[18,35],ideal:22,idl:34,ignor:[22,28],imag:[6,22],immedi:[11,23],implement:[3,28,33],inaccess:22,includ:[2,3,17,19,21,23,28,33],increment:[31,34],index:[15,17,19,21,23,32,34],indexchang:6,info:21,inform:[19,21],initi:[21,23,28],initui:[6,7],input:22,instal:[18,35],instanc:[2,6,17,19,22,28,33],instanti:[17,19,22,23,28,33],inter:3,interfac:[0,18],intern:3,interpret:[16,21],interrupt:3,interv:3,introduc:3,involv:[19,21,28],item:6,itemassignmentwidget:6,iter:[3,4],its:[3,19,22,23],itself:28,java:[19,21],join:23,just:[16,23,33],keep:16,kei:28,kept:16,keyword:[3,23,28,34],kind:21,kw:[6,9],kwarg:[3,6,7,9,11,14,17,28,29,30,31,32,33,34],label:6,labjack:[1,2,11],languag:[19,21],last:23,layout:[33,34],learn:[16,17,35],left:16,level:21,librari:[0,18,19,21],like:[16,23,33],line:[22,35],link:[6,21],list:[2,3,4,6,16,28],littl:[19,21],loadprotocol:6,local:16,locat:16,log:[21,23],loop:[22,23,31,33,34],lower:16,m:[6,19,35],mai:[3,19,21,22,23,35],main:[1,2,15,17,19,21,22,23,28,29,30,31,32,33],mainwindow:6,major:[19,21],make:[16,17,21,28],manag:16,mani:[19,21],manual:[19,21],map:[23,28,29,30,33],matlab:[19,21],maximum:22,maxval:[6,9],me:33,mean:[19,21,23],mearn:[0,18],mention:23,mess:35,messag:[0,2,3,17,18,19,22,23,31,32,33,34],message_tag:4,metaclass:14,method:[3,4,6,7,17,19,21,22,23,28,29,30,31,32,33,34],might:[0,16,17,18,22],migrat:[23,28],millisecond:3,mind:[0,18],minimum:23,minval:[6,9],mode:3,modifi:16,modul:[1,15,17,28,29,30,31,32,33,34],modular:[0,18],modulewidget:[17,33],more:[19,21,23],moreov:[19,21],most:[19,28],mpg:[0,18],msec:3,multipl:[19,21,23],must:[16,17,19,21,22,23,28,29,30,31,33,34],my_ev:17,my_method:17,my_modul:17,my_work:17,mywidget:17,mywork:17,n:[3,28,31,32],name:[2,3,6,7,9,11,14,17,19,21,23,28,29,30,31,32,33,34,35],navig:[16,35],ndarrai:[4,6],necessari:[19,21,23],need:[12,16,17,19,21,23,28],network:[0,17,18,19,21,23,28,29,31,34],networkconfigur:6,never:3,new_param:9,new_valu:6,newprotocol:6,newvalu:6,next:[2,3,16,23],node:[19,21],none:[2,3,6,9,11,19,21,33],note:[3,16,18,23,28],now:[16,17,31,32],np:[32,34],nsend:28,number:[3,22,34],numer:[19,21],numpi:[4,6,19,21,23,32,34],o:4,o_byt:4,obj:[4,6],object:[2,3,4,6,14,17,19,21,22,23,28,29,30,31,32],often:19,old:12,onc:[16,19,22,23,28,31,34],one:[3,19,21,23,28,29,31],onli:[3,19,22,28],open:[16,22],opencv:18,option:[2,3,6,23],optogenet:[2,8],optogeneticswidget:11,optogeneticswork:11,other:[0,3,16,17,18,19,21,22,23,33],our:[28,33,34],out:23,output:[19,21,22],over:[0,4,18,19,21,22],overrid:23,overridden:23,overview:[17,18],overwrit:23,own:[16,18,19,22,23,35],packag:1,pair:[19,21],panel:16,param:34,param_chang:9,param_dict:9,paramet:[2,3,4,6,23],parametergroupbox:9,parent:7,part:4,particular:[19,21],pass:[3,4,17,18,19,21,22,23,28,34],past:35,path:16,pattern:[19,21,22,28],peopl:19,pick:22,pike:[8,9],pip:16,pipe:[19,21],pipelin:23,plot:[11,33],plotter:[1,2,9,34],png:22,point:[33,34],poll:23,port:[2,17,19,21,22,23,28,29,30,31,32,33,34],portmanag:2,portmanteau:[0,18],possibl:16,power:[16,23],pre:[2,15,23],predefin:3,predomin:21,predominantli:21,prepend:[19,21],prevent:22,print:[28,29,30,31,32,33,34],privat:2,process:[1,2,11,17,21,23,28],processmixin:22,program:[19,21,22],project:[16,35],prompt:16,properli:[16,17,19,21,28],properti:[2,6,7,9,14],protect:[22,23],protocol:[1,2],protocol_widget:[2,6],protocolbuild:6,protocolwidget:7,protocolwindow:6,provid:[17,19,21,22,23],pub:[4,19,21,22],publish:[2,19,21,22,23],publisherconfig:2,pull:[19,21,22],push:[19,21,22],put:17,py:[16,35],pycharm:16,pydra:[15,28,29,30,31,32,34,35],pydra_cheatsheet:22,pydra_env:[16,35],pydra_test:34,pydrabackend:19,pydraconfig:2,pydradockwidget:6,pydramain:[2,19],pydramessag:[4,18],pydraobject:[2,4,11,18,22],pydraprocess:22,pyqt5:[3,6,7,9,33,34],pyqt:[0,18,33],pyqtgraph:6,pyqtslot:33,python:[0,16,18,35],qbuttonadd:6,qcloseev:6,qcombobox:6,qcomboboxlink:6,qdialog:6,qdockwidget:6,qformlayout:34,qgroupbox:[6,7,9],qmainwindow:6,qobject:3,qpushbutton:[6,7,33],qspinbox:34,qt:[3,17,33],qtcore:[3,33],qtimer:3,qtoolbar:7,qtwidget:[6,7,9,33,34],question:[0,16,18],queu:3,queue:[3,19,21],quickli:22,quit:16,qvboxlayout:33,qwidget:6,rand:[32,34],random:[32,34],rang:30,rate:34,rather:[19,21,23],reach:33,read:2,reader:4,readi:16,receiv:[2,3,4,6,17,19,21,22,23,28,29,30,31,32,34],receivelog:[6,9],receiverconfig:2,recommend:16,record:[7,34],record_button_click:7,recordbutton:7,recordingtoolbar:7,recv:[2,4],recv_:23,recv_fram:[17,23,32,34],recv_index:[17,23,32],recv_timestamp:[17,23,31,32],regist:14,rejoin:28,rememb:[23,34],remov:6,rep:3,repeat:3,repetit:3,repositori:18,repres:4,request:19,requir:[19,22,23],reset:[3,14],respect:[19,21],respond:[17,28],restart:22,reus:22,right:16,row:[6,9],rowcount:6,run:[2,3,6,16,18,19,21,22,23,28,33,34,35],run_protocol:6,s:[4,17,19,21,23,28,29,30,31,32,33,34,35],s_byte:4,same:[4,23,34],sampl:35,save:[2,3,22,23],saveprotocol:6,saver:[2,19,21,22],saverconfig:2,script:[17,33,35],sec:3,second:[28,29,30,31],section:[23,35],see:[16,19,21,35],select:16,selectionchang:6,self:[6,17,28,29,30,31,32,33,34],send:[4,19,21,23,28,29,32,33,34],send_data:32,send_ev:[6,17,23,28,29,30,32,33,34],send_fram:[17,23,32,34],send_index:[17,23,32,34],send_sign:14,send_timestamp:[17,23,31,32],sender:[2,32],senderconfig:2,sendev:6,sent:[4,19,21,23],separ:[6,23,28],sequenc:3,serial:[2,3,19,21],serialize_arrai:4,serialize_bool:4,serialize_dict:4,serialize_float:4,serialize_int:4,serialize_objet:4,serialize_str:4,serv:[19,21],set:[3,6,16,30,33,34],set_filenam:7,set_param:9,set_valu:[9,34],set_working_directori:7,seten:34,setflag:3,setinterv:3,setlayout:[33,34],setprotocol:6,setrepetit:3,setup:[0,16,18,23,28],setvalu:6,shape:32,should:[16,19,23,28,33,34],show_protocol:7,signal:[3,17,21,22,23,28,33],signatur:[19,21],signifi:19,significantli:23,similar:23,simpl:[19,21,22,23],simplic:[0,18],simul:34,sinc:[16,19,21,23,28],singl:[19,21,22,28],singleton:19,sleep:[28,29,30,31,32,34],slot:[17,33],so:[3,17,22],sock:4,socket:[4,19,21,22,23],socktyp:4,some:[17,23,33,34,35],someth:[17,22],sometim:17,soon:3,sourc:[2,3,4,6,7,9,11,14,16,23,29,30,31,32,33],spam:[29,30,31,32],spam_ev:[29,30],spamwork:[29,30,31],special:[3,21,23],specif:[19,21,23],specifi:[4,23],spew:22,spinbox:34,spinboxwidget:6,stackoverflow:16,stamp:34,start:[2,3,16,17,28,33],start_record:[6,23],startrecord:[6,7],state:[1,2,7,34],stateen:[6,7],steep:16,still:22,stimulation_off:11,stimulation_on:11,stop_record:[6,23],store:[2,34],str:[2,3,4,6,19,21],string:[4,19,21,23],string_format:[1,2],stuck:22,sub:[2,19,21,22],subclass:[17,19,21,23,31,33],submodul:[1,8,12],subpackag:1,subscrib:[22,23],subscriberconfig:2,subscript:[2,17,21,23,29,31,32,34],substanti:28,suffix:6,summar:19,sure:[16,17,28],synchron:14,system:[0,18],t0:14,t:[14,17,19,21,31,32,34],tag:[4,19,21,23],tail_track:[8,12],take:[23,28,30],target:[19,21,33],task:23,tcp:[19,21],teach:35,termin:[11,16,17,22,23],test:17,than:[17,19,21,23],thei:[19,22,23],them:[4,17,19,21,22,23],themselv:19,therefor:23,thi:[0,16,17,18,19,21,22,23,28,33,34,35],thing:23,those:[0,17,18,23],thread:[2,3],three:[19,21,23],through:[16,17,19,21,34],throughout:31,thu:22,time:[3,28,29,30,31,32,34],timed_out:3,timeout:3,timer:3,timerwidget:6,timestamp:[4,14,17,19,21,23,31,32,34],togeth:23,toggle_autonam:7,toggle_las:11,toggle_vis:6,toolbar:[2,6],top:[16,21],track:[2,8,19,21,34],trackingoverlai:34,trackingwork:34,trigger:[1,2,19,21],trigger_receiv:3,triggercontain:3,tupl:[2,4],tutori:[17,35],two:[19,21,23],type:[3,4,14,16,18,19,21,23],typic:[19,21,22],uint8:34,under:[19,21,28],underscor:19,understand:[19,21],understood:32,unidirect:[19,21],uniqu:[4,19,21,23,28,29,30,31,34],unless:28,unpack:28,until:[3,23],up:22,updat:[6,12,23],update_en:6,update_filenam:7,update_plot:6,update_protocol:7,updatechildren:6,updateimag:6,updateoverlai:[6,34],updateparam:6,updateplot:[6,9,11,34],updateui:6,us:[2,3,14,15,16,18,19,21,23,28,33,34,35],usag:19,user:[0,2,16,19,23],usernam:16,util:[1,2,11,15],val:[2,6,7,14,34],valu:[4,6,7,9,23,30,31,34],value_widget:34,valuechang:[6,34],variou:[19,21],veri:[19,21],version:[12,16],via:[0,18,19,21,22,23],video:[19,21],w:19,wa:[31,33,34],wai:[19,35],wait:[3,31],want:[16,17,19,21,23,33],we:[28,33,34],welcom:18,well:[22,23],were:33,what:35,when:[3,19,21,22,23,28,29,30,33],whenev:[17,28,31,32,33,34],where:[16,19,22,35],wherebi:3,whether:[3,23,28],whew:16,which:[3,16,17,19,21,22,23,28,33],whichev:16,whilst:23,whom:23,whose:23,widget:[1,2,8,12,18,33,34],window:[6,16],wish:19,within:[3,19,21,22,23,28],without:[16,17,23,35],won:17,work:[16,17,19,23,35],worker:[0,1,2,8,9,18,19,21,22,28,30,32,33,34],workerconfig:2,working_dir:34,world:[18,32,33],worri:[19,23],wrapper:[4,33],write:2,x:[6,34],ximea:[8,9],y:[6,34],yml:16,you:[16,17,19,21,33,35],your:[18,35],zeromq:[0,17,18,22,23],zmq:[2,4]},titles:["Pydra - experiment control","pydra","pydra package","pydra.core package","pydra.core.messaging package","pydra.core.saving package","pydra.gui package","pydra.gui.toolbar package","pydra.modules package","pydra.modules.cameras package","pydra.modules.cameras.workers package","pydra.modules.optogenetics package","pydra.modules.tracking package","pydra.modules.tracking.tail_tracker package","pydra.utilities package","API Guide","Installation","Using Pydra","Pydra - experiment control","Overview of Pydra","Overview","Messaging in Pydra","Pydra network","PydraObjects","GUI","Qt events","Pydra modules","Pipelines","Hello world","Communication between workers","Events with arguments","Passing data between workers","Data types","Pydra gui","Advanced functionality","Welcome!"],titleterms:{"function":34,"import":17,A:[19,21],ad:17,add:16,addit:16,advanc:34,api:[15,18],argument:30,base:3,between:[19,29,31],camera:[9,10],clock:14,clone:16,commun:[19,29],configur:[2,16],connect:6,content:[2,3,4,5,6,7,8,9,10,11,12,13,14],control:[0,18],core:[3,4,5],creat:17,data:[31,32],directory_widget:7,displai:6,environ:16,event:[25,30],experi:[0,18],file_nam:7,fork:16,get:18,github:16,gui:[6,7,17,24,33],guid:[15,18],hello:28,id:16,instal:16,labjack:14,librari:16,main:6,messag:[4,21],modul:[2,3,4,5,6,7,8,9,10,11,12,13,14,26],network:22,note:[19,21],opencv:16,optogenet:11,overview:[19,20],own:17,packag:[2,3,4,5,6,7,8,9,10,11,12,13,14],pass:31,pike:10,pipelin:27,plotter:6,process:[3,22],protocol:[3,6,25],protocol_widget:7,pydra:[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,21,22,23,26,33],pydramessag:[19,21],pydraobject:[19,21,23],qt:25,repositori:16,run:17,save:5,saver:23,serial:4,start:18,state:6,string_format:14,structur:18,submodul:[2,3,4,5,6,7,9,10,11,13,14],subpackag:[2,3,6,8,9,12],tail_track:13,thread:5,toolbar:7,track:[12,13],trigger:[3,25],tutori:18,type:32,us:17,user:18,util:14,welcom:35,widget:[6,9,11,13,17],worker:[3,10,11,17,23,29,31],world:28,ximea:10,your:[16,17],zeromq:[19,21]}})