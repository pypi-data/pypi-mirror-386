// js/import-text-block.js

class MountVideoDefinition extends window.wagtailStreamField.blocks
    .StructBlockDefinition {
    render(placeholder, prefix, initialState, initialError) {
        const block = super.render(
            placeholder,
            prefix,
            initialState,
            initialError,
        );

       
        return block;
    }
}

window.telepath.register('mediaflowvideo.MediaflowVideoBlock', MountVideoDefinition);
console.info('telepath path registered for mediaflowBlock')
