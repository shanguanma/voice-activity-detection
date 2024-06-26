#!/usr/bin/env bash

stage=0
stop_stage=100
. path.sh
. utils/parse_options.sh

if [ ${stage} -le -1 ] && [ ${stop_stage} -ge -1 ];then
   echo "prepare kaldi format for  magicdata-RAMC data"
   python prepare_magicdata_180h.py
fi

if [ ${stage} -le 0 ] && [ ${stop_stage} -ge 0 ];then
   echo "prepare vad  magicdata-RAMC format data for train vad model "
   data_path=/home/maduo/codebase/fairseq_speechtext/examples/speaker_diarization/data/magicdata-RAMC/
   #for name in train dev test;do
   for name in train  test;do
      python prepared_vad_data_for_magicdata-RAMC.py \
	      --data_path $data_path \
	      --type $name
   done
fi
if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ];then
   echo "train a vad model using magicdata-RAMC dataset "
	CUDA_VISIBLE_DEVICES=0 python main.py train tests/configs/vad/train_config_magicdata-RAMC.yaml

fi


if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ];then
   echo "generate vad json file using pretrain transformer vad model "
   #echo "transformer vad model is from https://github.com/voithru/voice-activity-detection/blob/main/tests/checkpoints/vad/sample.checkpoint"
   echo "I used my pretrain vad model to get testset vad segement of magicdata-RAMC"
   vad_code=/home/maduo/codebase/voice-activity-detection
   vad_model=/home/maduo/codebase/voice-activity-detection/results/tests/vad/magicdata-RAMC-sample/v001/checkpoints/vad-magicdata-RAMC-sample-v001-epoch-019-val-acc-0.92249.checkpoint
   data=data/magicdata-RAMC/test/
   #output_dir=$data/predict_vad
   #mkdir -p $output_dir
   vad_threshold="0.2 0.22 0.24 0.25 0.27 0.28 0.29 0.30 0.31 0.32 0.34 0.36 0.38"
   for name in $vad_threshold;do
    for audio_path in `awk '{print $2}' $data/wav.scp`;do
      audio_name=$(basename $audio_path | sed s:.wav$::)
      echo "audio_path : $audio_path"
      output_dir=$data/predict_vad_${name}
      mkdir -p $output_dir
      python  $vad_code/main.py predict \
            --threshold $name \
            --output-path $output_dir/${audio_name}.json \
            $audio_path\
            $vad_model
   done
  done
 fi

## the above script is used to display how to train a vad using a dataset (i.e. magicdata-RAMC diarization dataset)


## How to use the above predict vad json file, the example(a diarization task) is display at my other repositories
# https://github.com/shanguanma/fairseq_speechtext/tree/main/examples/speaker_diarization/scripts/magicdata-RAMC
