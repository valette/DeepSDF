"use strict";
console.clear();

const { desk, qx, THREE, ACVD, require } = window;
const { join } = require( "path" );

const params = {

//    referenceDir : "indiana/incisor/",
    referenceDir : "openData/Surfaces externes",
    deepSDFDir : "DeepSDFModels/",
    maxDistance : 0.5,
    direction : 1,
    trimBegin : "_ext",
//    modelIds : [ 19, 20, 21, 22, 23, 24, 25 ],
    modelIds : [ 56, 57, 58, 59, 60, 61 ],
//    modelIds : [ 56],
    opacity : 1,
    wireframe : false,
    prependParentDir : false,
    maxLength : -1,
    ...window?.DeepSDF?.diffTool2Params,
};

desk.URLParameters.parseParameters( params );
const viewer = new desk.THREE.Viewer();
if ( desk.auto ) viewer.fillScreen();

const container = new qx.ui.container.Composite();
container.setLayout( new qx.ui.layout.VBox( 5 ) );
container.setWidth( 200 );
viewer.getWindow().addAt( container, 0 );
const referenceDir = new desk.FileField( params.referenceDir );
container.add( new qx.ui.basic.Label( "Database directory:") );
container.add( referenceDir );
const deepSDFDir = new desk.FileField( params.deepSDFDir );
container.add( new qx.ui.basic.Label( "Models directory:") );
container.add( deepSDFDir );
const modelIds = new desk.FileField( params.modelIds.join( ",") );
container.add( new qx.ui.basic.Label( "Models:") );
container.add( modelIds );
modelIds.addListener( "changeValue", updateModels );
container.add( new qx.ui.basic.Label( "Trim begin in file name:") );
const trimBegin = new desk.FileField( params.trimBegin );
container.add( trimBegin );

const prependParentDir = new qx.ui.form.CheckBox("Prepend parent dir to name" );
prependParentDir.setValue( params.prependParentDir );
container.add( prependParentDir );
const list = new qx.ui.form.List();
const listLabel = new qx.ui.basic.Label( "Reconstructions:");
container.add( listLabel );
container.add( list, { flex : 1  } );
const downloadDistances = new qx.ui.form.Button( "Download distances" );
container.add( downloadDistances );

for ( let widget of [ referenceDir, deepSDFDir, prependParentDir, trimBegin ])
    widget.addListener( "changeValue", updateList );


downloadDistances.addListener( "execute", () => {
    const size = ["latentCodeSize" ];
    const max = [ "maxError" ];
    const average = [ "averageError" ];

    for ( let model of models ) {
        size.push( model.specs.CodeLength );
        max.push( model.distances.max );
        average.push( model.distances.average );
    }

    const text = [ size, max, average ].map( a => a.join( "," ) ).join( '\n' );
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', list.getSelection()[ 0 ].getLabel() + ".csv" );
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

} );

const downloadAllDistances = new qx.ui.form.Button( "Download all distances" );
downloadAllDistances.addListener( "execute", computeAndDownloadAllDistances );
container.add( downloadAllDistances );

let referenceMesh;

const colorBar = ACVD.getColorBar( params.maxDistance );
viewer.add( colorBar, { bottom : 50, left : "10%", width : "80%" } );

const wireframe = new qx.ui.form.CheckBox( "wireframe" );
viewer.add( wireframe, { bottom : 20, left : 5 } );
wireframe.setValue( params.wireframe );
wireframe.addListener( "changeValue", updateAllViews );

const opacity = new qx.ui.form.Slider();
viewer.add( opacity, { bottom : 1, left : 0, width : "50%" } );
opacity.setValue( Math.floor( params.opacity * opacity.getMaximum() ) );
opacity.addListener( "changeValue", updateAllViews );

function updateAllViews() {
    for ( let items of [ { mesh : referenceMesh, viewer }, ...models].map( m => [ m.mesh, m.viewer ] ) )
        updateMeshView( ...items );
}

function updateMeshView( mesh, viewer ) {

    if ( !mesh ) return;
    let edges = mesh.userData.edges;
    mesh.material.transparent = true;

    if ( wireframe.getValue() ) {

        if ( !edges ) {

            const material = new THREE.MeshBasicMaterial( { color : 0x000000, wireframe : true } );
            edges = new THREE.Mesh( mesh.geometry, material );
            mesh.userData.edges = edges;
            mesh.add( edges );
        }
        mesh.material.opacity = 0;
        edges.visible = true;

    } else  {

        if ( edges ) edges.visible = false;
        mesh.material.opacity = opacity.getValue() / opacity.getMaximum();

    }

    viewer.render();

}

let database, models = [];

async function updateModels() {

    const viewers = models.map( model => model.viewer );

    models = modelIds.getValue().split( "," ).map( (id, index ) => {
        const viewer2 = viewers.pop() || new desk.THREE.Container();
        viewer2.setDecorator( "main" );
        viewer2.link( viewer );
        viewer.getWindow().add( viewer2, { flex : 1 } );
        return { index, viewer : viewer2, id };
    } );

    viewers.forEach( viewer => viewer.destroy() );

    updateList().catch( console.warn );

}


list.addListener("changeSelection", async function (e) {

    const selection = e.getData();
    if ( !selection[ 0 ] ) return;

    try {

        viewer.removeAllMeshes();
        container.setEnabled( false );
        const label = selection[ 0 ].getLabel();
        const originalMesh = database[ label ];
        const promises = [ viewer.addFileAsync( originalMesh ) ];

        promises.push( ...models.map( async model => {
            model.viewer.removeAllMeshes();

            if ( !model.specs ) {

                const specsFile = join( deepSDFDir.getValue().split( "*" )[ 0 ], model.id, "specs.json" );
                if ( await desk.FileSystem.existsAsync( specsFile ) )
                    model.specs = JSON.parse( await desk.FileSystem.readFileAsync( specsFile ) );
                else model.specs = {};

                model.label = model.viewer.getUserData( "label" );
                if ( !model.label ) {
                    model.label = new qx.ui.basic.Label( "" );
                    model.viewer.add( model.label, { left : 0, bottom : 10, width : "100%" } );
                    model.label.set( { rich : true } );
                    model.viewer.setUserData( "label", model.label );
                }
            }

            const reconstruction = model.reconstructions[ label ];
            delete model.distances;
            if ( !reconstruction ) {
                model.label.setValue( "Nothing here" );
                return;
            }

            model.label.setValue( "Computing" );
            const distance = await ACVD.getDistanceBetweenMeshes(
                reconstruction, originalMesh );
            const colors = await ACVD.loadMeshWithColors( distance, params.maxDistance, { label : "reconstruction" } );
            const distances = colors.geometry.attributes.Distance;
            let max = 0, average = 0;

            for ( let i = 0; i < distances.count; i++ ) {
                const d = distances.getX( i );
                max = Math.max( max, d );
                average += d / distances.count;
            }

            model.viewer.addMesh( colors, { label : reconstruction.split( "/" ).pop() } );
            model.mesh = colors;
            model.label.setValue( "Latent size : " + model.specs.CodeLength +
                "<br> distances : "+
                "<br> average : "+ average.toPrecision( 4 ) +
                "<br> max : " + max.toPrecision( 4 )
            );
            model.distances = { average, max };
            updateMeshView( colors, model.viewer );
        } ) );

        await Promise.all( promises );
        referenceMesh = await promises[ 0 ];
        updateMeshView( referenceMesh, viewer );

    } catch( e ) {
        console.warn( e );
        
    } finally {
        container.setEnabled( true );

    }
});

async function updateList() {
try{
    list.removeAll();
    listLabel.setValue( "0 reconstructions" )
    const promises = [ getMeshes( referenceDir.getValue() ) ];

    promises.push( ...models.map( async model => {
        const { id } = model;
        const dir = deepSDFDir.getValue().includes( "*" ) ?
            deepSDFDir.getValue().replace( "*", model.id ) :
            join( deepSDFDir.getValue(), model.id );
        model.reconstructions = await getMeshes( dir );
    } ) );

    const names = new Set();
    await Promise.all( promises );
    database = await promises[ 0 ];
    const meshArray = Object.keys( database );
    meshArray.sort();

    for ( let model of models ) {
    
        for ( let meshName of meshArray ) {

            if ( !model.reconstructions[ meshName ] ) continue;

            if ( ( ( params.maxLength < 0 ) || list.getChildren().length < params.maxLength ) &&
                !names.has( meshName ) ) {

                const item = new qx.ui.form.ListItem( meshName );
                list.add(item);
                names.add( meshName );
            }

        }
    }

    for ( let model of models ) model.viewer.removeAllMeshes();
    viewer.removeAllMeshes();
    if ( list.getChildren().length ) list.setSelection( [ list.getChildren()[ 0 ] ] );
    listLabel.setValue( list.getChildren().length + " reconstructions:" )

} catch( e ) {console.warn( e ) };
}

updateModels().catch( console.warn );

async function getMeshes( dir ) {

    const files = {};
    if ( ! await desk.FileSystem.existsAsync( dir ) ) return files;
    await desk.FileSystem.traverseAsync( dir, file => {

        for ( let extension of [ ".vtp", ".stl", ".ply" ] )
            if ( file.toLowerCase().endsWith( extension ) ) {
                const path = file.split( "/" );
                let name = path.pop()
                    .split( "." ).slice( 0, -1 ).join( "." )
                    .split( " " ).join( "_" )
                    .split( trimBegin.getValue() )[ 0 ];
                if ( prependParentDir.getValue() )
                    name = path.pop() + "_" + name;
                files[ name ] = file;
            }

    } );

    return files;

}

async function computeAndDownloadAllDistances() {

    container.setEnabled( false );
    const data = [ [ "model", "mesh", "average_distance_original_to_reconstruction", "average_distance_reconstruction_to_original", "hausdorff" ] ];

    for ( let model of models ) {

        downloadAllDistances.setLabel( "Computing for model : " + model.id );

        const promises = list.getChildren().map( async child => {
            const label = child.getLabel();
            const original = database[ label ];
            const reconstruction = model.reconstructions[ label ];
            if ( !reconstruction ) return [];
            const d1 = await ACVD.getAverageDistanceBetweenMeshes( original, reconstruction );
            const d2 = await ACVD.getAverageDistanceBetweenMeshes( reconstruction, original );
            const h = await ACVD.getHausdorffDistanceBetweenMeshes( original, reconstruction );
            return [ model.id, label, d1, d2, h ];
        } );

        data.push( ...( await Promise.all( promises ) ).filter( a => a.length ) );

    }

    container.setEnabled( true );
    downloadAllDistances.setLabel( "Download all distances" );
    const txt = data.map( l => l.join( "," ) ).join( "\n" );
    ACVD.downloadText( txt, "distances.csv" );

}