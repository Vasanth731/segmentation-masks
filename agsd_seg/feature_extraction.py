import torch
import torch.nn as nn
from torchvision import models


def featureL2Norm(feature):
    epsilon = 1e-6
    norm = torch.pow(torch.sum(torch.pow(feature, 2), 1) +
                     epsilon, 0.5).unsqueeze(1).expand_as(feature)
    return torch.div(feature, norm)


class FeatureExtraction(torch.nn.Module):
    def __init__(self, train_fe=False, feature_extraction_cnn='vgg19', normalization=True, last_layer='', use_cuda=True):
        super(FeatureExtraction, self).__init__()
        self.normalization = normalization

        # multiple extracting layers
        last_layer = last_layer.split(',')

        if feature_extraction_cnn == 'vgg16':
            self.model = models.vgg16(pretrained=True)
            # keep feature extraction network up to indicated layer
            vgg_feature_layers = ['conv1_1', 'relu1_1', 'conv1_2', 'relu1_2', 'pool1', 'conv2_1',
                                  'relu2_1', 'conv2_2', 'relu2_2', 'pool2', 'conv3_1', 'relu3_1',
                                  'conv3_2', 'relu3_2', 'conv3_3', 'relu3_3', 'pool3', 'conv4_1',
                                  'relu4_1', 'conv4_2', 'relu4_2', 'conv4_3', 'relu4_3', 'pool4',
                                  'conv5_1', 'relu5_1', 'conv5_2', 'relu5_2', 'conv5_3', 'relu5_3', 'pool5']

            start_index = 0
            self.model_list = []
            for l in last_layer:
                if l == '':
                    l = 'pool4'
                layer_idx = vgg_feature_layers.index(l)
                assert layer_idx >= start_index, 'layer order wrong!'
                model = nn.Sequential(
                    *list(self.model.features.children())[start_index:layer_idx + 1])
                self.model_list.append(model)
                start_index = layer_idx + 1

        if feature_extraction_cnn == 'vgg19':
            self.model = models.vgg19(pretrained=True)
            # keep feature extraction network up to indicated layer
            vgg_feature_layers = ['conv1_1', 'relu1_1', 'conv1_2', 'relu1_2', 'pool1',
                                  'conv2_1', 'relu2_1', 'conv2_2', 'relu2_2', 'pool2',
                                  'conv3_1', 'relu3_1', 'conv3_2', 'relu3_2', 'conv3_3', 'relu3_3', 'conv3_4', 'relu3_4', 'pool3',
                                  'conv4_1', 'relu4_1', 'conv4_2', 'relu4_2', 'conv4_3', 'relu4_3', 'conv4_4', 'relu4_4', 'pool4',
                                  'conv5_1', 'relu5_1', 'conv5_2', 'relu5_2', 'conv5_3', 'relu5_3', 'conv5_4', 'relu5_4', 'pool5']

            # vgg_output_dim = [64, 64, 64, 64, 64,
            #                   128, 128, 128, 128, 128,
            #                   256, 256, 256, 256, 256, 256, 256, 256, 256,
            #                   512, 512, 512, 512, 512, 512, 512, 512, 512,
            #                   512, 512, 512, 512, 512, 512, 512, 512, 512]

            start_index = 0
            self.model_list = []
            # self.out_dim = 0
            for l in last_layer:
                if l == '':
                    l = 'relu5_4'
                layer_idx = vgg_feature_layers.index(l)
                assert layer_idx >= start_index, 'layer order wrong!'
                # self.out_dim += vgg_output_dim[layer_idx]
                model = nn.Sequential(
                    *list(self.model.features.children())[start_index:layer_idx + 1])
                self.model_list.append(model)
                start_index = layer_idx + 1

        if feature_extraction_cnn in ['resnet18', 'resnet101']:

            if feature_extraction_cnn == 'resnet18':
                self.model = models.resnet18(pretrained=True)
            else:
                self.model = models.resnet101(pretrained=True)

            resnet_feature_layers = ['conv1',
                                     'bn1',
                                     'relu',
                                     'maxpool',
                                     'layer1',
                                     'layer2',
                                     'layer3',
                                     'layer4']

            resnet_module_list = [self.model.conv1,
                                  self.model.bn1,
                                  self.model.relu,
                                  self.model.maxpool,
                                  self.model.layer1,
                                  self.model.layer2,
                                  self.model.layer3,
                                  self.model.layer4]

            start_index = 0
            self.model_list = []
            for l in last_layer:
                if l == '':
                    l = 'layer3'
                layer_idx = resnet_feature_layers.index(l)
                assert layer_idx >= start_index, 'layer order wrong!'
                model = nn.Sequential(
                  *resnet_module_list[start_index:layer_idx + 1])
                self.model_list.append(model)
                start_index = layer_idx + 1

        if not train_fe:
            # freeze parameters
            for param in self.model.parameters():
                param.requires_grad = False
        # move to GPU
        if use_cuda:
            self.model_list = [model.cuda() for model in self.model_list]

    def forward(self, image_batch):
        features_list = []
        features = image_batch
        for model in self.model_list:
            features = model(features)
            if self.normalization:
                features = featureL2Norm(features)
            features_list.append(features)
        return features_list
    

